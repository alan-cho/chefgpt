# Deployment (AWS)

The following sections cover the key infrastructure decisions for deploying this application on AWS.

## Compute Choice (Fargate):

The simplicity of this application doesn't warrant the fine control offered by EC2 and EKS.
Lambda's cold starts and maximum execution time make it a poor fit for a stateful streaming agent; Fargate containers stay warm.
Fargate is the best choice since it abstracts the complexity of managing the infrastructure. Additionally, Fargate tasks are easy to set up with containers and they can be scaled automatically.

## Secret Management

Parameter Store is appropriate given the simplicity of this application. There are only two API keys that need to be injected at runtime (`ANTHROPIC_API_KEY`, `SERPER_API_KEY`). Secrets Manager is more capable, allowing key rotation and adding policies to secrets. In the near future, especially if databases were added (higher risk), Secrets Manager would be worth the cost tradeoff and slight increase in complexity.

## Observability

- **Application**: JSON logging within the backend container itself. The structure of the log could look something like:
  `{ request_id, user_id, latency, error }`
  Send the logs to AWS CloudWatch, which can capture the output of containers running on ECS Fargate. Additionally, add alarms on CloudWatch for specific triggers, like p99 latency, server error rates, etc.
- **Infrastructure**: Eventually, add X-Ray to view the latency of the end-to-end flow and time spent at each point (load balancer, API, etc). Not necessary at low scale.
- **LLM**: LangSmith to see the metrics and latency of the agent itself. Easier to debug prompts/flows, measure performance, and track costs (time-to-first-token, latency, output quality/datasets, regression testing).

## Scaling & Network

At first, ECS Fargate can scale horizontally, which should be bounded by I/O. Scale based on request count per ECS task, and if needed, scale by CPU utilization.
Add a load balancer that pings for health checks to prevent routing to dead tasks.
For the VPC, the public subnet should contain the load balancer and the private subnet should contain the ECS tasks. The private subnet firewall should only allow traffic from the load balancer. If a database is added, it should also live in a separate private subnet that only allows ingress from the ECS tasks.
To tackle availability, add additional availability zones (e.g. US-virginia-1a and US-virginia-1b). Additionally, a CDN can improve performance for frontend caching.

Flow: `User -> CDN -> Load Balancer -> ECS -> DB -> ECS -> Anthropic`

## Auth & Security

Use API keys that are hashed in the database for low scale. Can start off with rate limiting per API key handled at the API level.
CORS should only allow the frontend domain (`allow_origins`).
Input validation should be handled by Pydantic schema, restricting the input (e.g. add a max length to query). Similarly, output is restricted by the Pydantic schema as well.
Some safeguards include filtering the output of the LLM (for leaked system prompts or unwarranted tool calls), limit tool permissions to the minimum required, and separate input from output so user input can't be injected into system prompts.
Specific to Anthropic, they are actively working on classifiers to protect against injection vulnerabilities, and models are already trained to be resilient to such prompts:

- [Mitigating Jailbreaks](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks) — guidance on hardening prompts and output filtering against adversarial inputs
- [Prompt Injection Defenses](https://www.anthropic.com/research/prompt-injection-defenses) — research on detecting and blocking prompt injection at the model level
- [Constitutional Classifiers](https://www.anthropic.com/news/constitutional-classifiers) — Anthropic's classifier-based approach to enforcing safety constraints

API keys (`ANTHROPIC_API_KEY`, `SERPER_API_KEY`) should be managed by AWS Secrets Manager for production workloads.
Eventually, as scale grows and stronger authentication is required: use OAuth2 + JWT. It allows token management and expiration, and supports role limiting. If a public API were exposed, adding an AWS API Gateway would be better as it supports authentication (JWT + OAuth2) and rate limiting built-in.

## ELT Integration

I'd suggest using a simple flow assuming real-time analytics are not required.

Flow: `Event -> DB -> Data Warehouse -> dbt -> Analytics`

After the `what_can_i_make` intent is classified, it writes a `recipe_event` to a lightweight SQL table. A scheduled cron job extracts from the table and writes to a data warehouse (AWS Redshift). Use dbt to transform the events into analytics that can be displayed on a dashboard. Note: pre-optimize by batching inserts for data warehouses.

Some metrics to consider:

- **Popular recipes** → recipe request count, cuisine/meal type count, current trends
- **Ingredient usage** → ingredient count, seasonal trends, common pairings
- **Missing cookware** → most commonly missed items, how many are missing per recipe
- **Web search usage** → how often does the LLM need external info (gaps in knowledge)
- **User metrics** → query counts per user, intent distribution

If real-time analytics are needed, a pub/sub system that writes directly to the data warehouse would be a better fit.

---

## Application Design & Trade-offs

This section documents the key architectural decisions made in the application itself and the reasoning behind them.

### Graph-based Orchestration (LangGraph)

The backend uses [LangGraph](https://langchain-ai.github.io/langgraph/) to model the agent as an explicit directed graph rather than a monolithic prompt or a simple LLM chain.

**Why a graph?** Cooking queries have meaningfully different shapes. A user asking "what can I make with these leftovers?" needs clarification and cookware validation before a recipe is generated. A user asking "what temperature do I roast chicken at?" needs none of that — it should go straight to the `assistant` node. Encoding these paths as explicit edges makes the routing visible and testable, as opposed to embedding all branching logic inside a single prompt.

**Graph topology:**

```
classify ──► respond_not_cooking
         │
         ├──► assistant ◄──► tools
         │
         └──► inquire ──► check_cookware ──► generate_recipe ◄──► tools
```

The entry point is always `classify`. From there, three paths are possible: reject non-cooking queries, send general questions to `assistant`, or route recipe-oriented queries through the longer `inquire → check_cookware → generate_recipe` pipeline.

**Trade-off:** Adding a `classify` LLM call to every request adds latency (~200–400ms). The alternative — letting the main LLM decide what to do — would reduce latency but makes routing implicit and harder to debug. Structured output on `classify` (see below) makes the routing deterministic, which is worth the extra call.

---

### Structured Output for Deterministic Routing

Three nodes — `classify`, `inquire`, and `check_cookware` — use `.with_structured_output()` backed by Pydantic models (`ClassificationResult`, `ClarifyingQuestion`, `CookwareRequirement`). This forces the LLM to return valid, typed JSON that the router functions can branch on without parsing or guarding against malformed output.

The alternative is prompt engineering ("respond with only 'yes' or 'no'"), which is brittle and breaks on model updates. Structured output is the right default for any node whose output drives control flow.

---

### Human-in-the-Loop via `interrupt`

The `inquire` node uses LangGraph's `interrupt()` primitive to pause graph execution mid-run and surface a clarifying question to the user. The frontend receives an `interrupt` SSE event containing the question and the `thread_id`, prompts the user for their answer, and resumes the graph by posting to `/query` with `resume` set to the answer.

This is preferable to prompting the main LLM to ask a question in its response and then parsing that response — the `interrupt` pattern makes the pause/resume lifecycle explicit in the graph rather than implicit in the output format. The `InMemorySaver` checkpointer persists the graph state between the pause and resume, so no state is re-computed.

**Trade-off:** The interrupt flow requires the frontend to be stateful enough to store the `thread_id` and detect the `interrupt` event type. A simpler API would stream the full response and let the LLM embed a follow-up question in the text — but that loses the ability to programmatically distinguish "the assistant needs input" from "the assistant is done."

---

### Separate LLM Instances Per Node

Each node that calls the LLM (`classify`, `inquire`, `check_cookware`, `assistant`, `generate_recipe`) instantiates its own `ChatAnthropic` client with specific configuration: structured output for classification nodes, tool bindings for generative nodes.

This separation is intentional. A node that classifies intent should never accidentally invoke a tool. A node that generates a recipe should never accidentally return a `ClassificationResult`. Isolating configuration per node makes each node's contract explicit and prevents unintended LLM capabilities from leaking across the graph.

**Trade-off:** Five LLM instances are created at module import time instead of one. The overhead is negligible (these are thin HTTP client wrappers), and the clarity benefit is significant.

---

### Streaming via Server-Sent Events

The `/query` endpoint uses FastAPI's `StreamingResponse` with `media_type="text/event-stream"` to push tokens to the frontend as they are generated. Streaming is filtered to `STREAMING_NODES = {"assistant", "generate_recipe"}` — the two nodes that produce user-visible text. Classification and cookware check outputs are internal and never streamed.

**Why SSE over WebSockets?** SSE is unidirectional (server → client), which matches the streaming use case exactly. WebSockets are bidirectional and add unnecessary handshake complexity for what is effectively a request-response stream. SSE is also simpler to implement, works over standard HTTP/2, and requires no special client library.

**Trade-off:** SSE connections are held open for the duration of a graph run. On Fargate, this means one connection per active user. The stateful streaming nature is one reason Lambda was ruled out — Lambda has a 15-minute execution limit and cold starts, both of which are problematic for streaming agents.
