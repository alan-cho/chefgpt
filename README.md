# ChefGPT

An AI cooking assistant that answers recipe questions, suggests ingredients, and explains techniques. Built with a FastAPI backend (LangGraph + Claude) and a Next.js frontend.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose, **or**
- Python 3.13+ and Node 20+ for local development

## Environment Setup

Copy the sample env files and fill in your API keys:

```bash
cp backend/.env.sample backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Then edit `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...   # Required — Claude API key
SERPER_API_KEY=...             # Required — web search (serper.dev)
DEBUG=false                    # Set to true to enable verbose backend logs
```

**Backend variables (`backend/.env`):**

| Variable            | Description                                                                |
| ------------------- | -------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY` | Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `SERPER_API_KEY`    | Search API key from [serper.dev](https://serper.dev)                       |
| `DEBUG`             | `true` enables INFO-level logs; `false` (default) silences them            |

**Frontend variables (`frontend/.env.local`):**

| Variable              | Description                                    |
| --------------------- | ---------------------------------------------- |
| `NEXT_PUBLIC_API_URL` | Backend base URL, e.g. `http://localhost:8000` |

## Running with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

To enable backend logs:

```bash
echo "DEBUG=true" >> backend/.env
docker compose up --build
```

## Running Locally

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend** (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## CI

GitHub Actions runs on every push and pull request to `main`:

- **Backend:** `ruff check` → `pytest` (no API keys required)
- **Frontend:** `eslint` → `next build` (includes TypeScript check)

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Running Tests

```bash
cd backend
pip install pytest pytest-mock
pytest -v
```

No API keys are required — all LLM calls are mocked.

## Architecture & Design

This section documents the key architectural decisions made in the application and the reasoning behind them.

### Graph-based Orchestration (LangGraph)

The backend uses [LangGraph](https://langchain-ai.github.io/langgraph/) to model the agent as an explicit directed graph rather than a monolithic prompt or a simple LLM chain.

**Why a graph?** Cooking queries have meaningfully different shapes. A user asking "what can I make with these leftovers?" needs clarification and cookware validation before a recipe is generated. A user asking "what temperature do I roast chicken at?" needs none of that — it should go straight to the `assistant` node. Encoding these paths as explicit edges makes the routing visible and testable, as opposed to embedding all branching logic inside a single prompt.

**Graph topology:**

```
classify ──► respond_not_cooking
         │
         ├──► assistant ◄──► tools
         │
         └──► inquire ──► check_cookware ──► generate_recipe ──► validate_recipe
                                                      ▲    │
                                                      └────┘ (via tools)
```

The entry point is always `classify`. From there, three paths are possible: reject non-cooking queries, send general questions to `assistant`, or route recipe-oriented queries through the longer `inquire → check_cookware → generate_recipe → validate_recipe` pipeline.

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

Each node that calls the LLM (`classify`, `inquire`, `check_cookware`, `assistant`, `generate_recipe`, `validate_recipe`) instantiates its own `ChatAnthropic` client with specific configuration: structured output for classification and validation nodes, tool bindings for generative nodes.

This separation is intentional. A node that classifies intent should never accidentally invoke a tool. A node that generates a recipe should never accidentally return a `ClassificationResult`. Isolating configuration per node makes each node's contract explicit and prevents unintended LLM capabilities from leaking across the graph.

**Trade-off:** Six LLM instances are created at module import time instead of one. The overhead is negligible (these are thin HTTP client wrappers), and the clarity benefit is significant.

---

### Recipe Validation as a Dedicated Node

The `validate_recipe` node sits between `generate_recipe` and the terminal state. It runs the generated recipe text through a structured-output LLM call that checks three things: safety (dangerous temperatures, harmful food combinations, allergen issues), structure (ingredients, instructions, and timing are all present), and hallucinations (implausibly large quantities or unrealistic temperatures).

**Why a separate node?** Embedding validation logic inside `generate_recipe` — either as a post-processing step or as additional prompt instructions — conflates generation with quality control and makes both harder to test in isolation. A dedicated node has a single responsibility, its own LLM configuration, and can be patched independently in tests without touching the generation node.

**Failure modes:** If the recipe is flagged as unsafe, the node appends a replacement `AIMessage` to the state. Because `main.py` reads `state["messages"][-1]` as the final response, the replacement is what the user receives. Structural issues (missing sections) are logged as warnings but pass through — re-generation on structure failure would require a conditional back-edge to `generate_recipe`, which adds graph complexity and latency; this is left as a future improvement.

**Trade-off:** Validation adds one extra LLM round-trip after every recipe generation. At typical Claude latencies this is ~500–800ms of additional wall time. The safety benefit justifies the cost, but the node should be monitored in production (via LangSmith or CloudWatch) to confirm the false-positive rate is low enough not to degrade the user experience.

---

## Timeboxing & Trade-offs

Given the scope of the project, the following decisions were made on what to build and what to defer:

**Prioritised:**

- End-to-end LangGraph flow (classify → route → generate → validate)
- Streaming SSE with interrupt/resume for human-in-the-loop
- Recipe validation node for safety and structure checking
- 28-test suite covering all nodes and routing logic
- CI/CD via GitHub Actions
- Docker Compose for reproducible local and deployment environments
- Thorough documentation (deployment, future work, design rationale)

**Cut and why:**

- **Zod types for API responses in the frontend** — the SSE event shapes are small and stable; adding Zod would add a dependency and boilerplate without meaningfully reducing risk at this scale
- **OpenAPI schema / generated client** — FastAPI auto-generates docs at `/docs`; a generated TypeScript client would be useful at larger scale but is over-engineering for a single endpoint
- **Persistent checkpointer (PostgreSQL/Redis)** — `InMemorySaver` is sufficient for the demo; adding a database would require schema migrations, connection pooling, and infrastructure that obscures the core LangGraph logic
- **Authentication** — no user identity means no auth; adding JWT/OAuth2 before there is a user model would be premature

---

## Known Limitations

The following are accepted limitations in the current implementation. See [`future.md`](future.md) for improvement plans.

- **Hardcoded cookware list** — `USER_COOKWARE` is a constant in `lib/constants.py`; no user profile persistence across sessions
- **In-memory graph state** — `InMemorySaver` means all thread state is lost on backend restart
- **Arbitrary input length cap** — `query` field is capped at 2000 characters; extremely long inputs were a DoS vector
- **No web search retry/circuit breaker** — a single Serper API failure previously crashed the graph; now retried with exponential backoff, but no circuit breaker yet
- **English-only prompts** — all system prompts are in English; non-English queries will be processed but responses may be inconsistent

---

## API

### `POST /query`

Send a question to the assistant.

**Request body:**

| Field       | Type    | Default  | Description                                    |
| ----------- | ------- | -------- | ---------------------------------------------- |
| `query`     | string  | required | The user's question (max 2000 characters)      |
| `thread_id` | string  | `null`   | Conversation thread ID (returned on interrupt) |
| `resume`    | string  | `null`   | Resume value after an interrupt                |
| `stream`    | boolean | `true`   | Stream tokens via SSE                          |
| `debug`     | boolean | `false`  | Return per-node graph trace                    |

### Example curl requests

**Basic streaming request:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I make a classic carbonara?"}' \
  --no-buffer
```

**Non-streaming request:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What can I substitute for buttermilk?", "stream": false}'
```

**Resume after an interrupt** (e.g. the assistant asked a follow-up question):

```bash
# The interrupt response contains a thread_id — use it to resume
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "", "thread_id": "<thread_id>", "resume": "I prefer spicy food"}'
```

**Debug mode** (returns per-node graph trace):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Best way to caramelize onions?", "stream": false, "debug": true}'
```

### Streaming response events

When `stream: true`, the endpoint returns `text/event-stream` with the following event types:

| `type`      | Description                                                   |
| ----------- | ------------------------------------------------------------- |
| `token`     | Partial text chunk (`content` field)                          |
| `interrupt` | Assistant needs more info (`question` and `thread_id` fields) |
| `response`  | Final complete response (`content` field)                     |
| `done`      | Stream finished                                               |
