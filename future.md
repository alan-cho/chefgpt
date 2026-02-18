# Future Work

This document covers planned improvements, known edge cases, and engineering work that would make ChefGPT production-ready at scale.

---

## User Preference Learning

**Current state:** `USER_COOKWARE` is hardcoded in `lib/constants.py`. The `user_preferences` field on `AppState` is populated per-session during the `inquire` node, but is discarded when the session ends.

**Improvement:** Introduce [LangGraph stores](https://langchain-ai.github.io/langgraph/concepts/memory/#long-term-memory) to persist user data across threads. A store is a key-value layer that sits outside the graph's thread-scoped checkpointer, so it's readable from any session.

What to persist per user:
- Available cookware (replaces the hardcoded constant)
- Dietary restrictions and preferences
- Cuisine preferences
- Past recipe ratings or feedback

This would allow the `generate_recipe` and `assistant` nodes to pull a user's profile at the start of each run and personalize without re-asking the same clarifying questions every time.

---

## Chat History Persistence

**Current state:** The graph uses `InMemorySaver` as its checkpointer. Threads exist only in memory — a backend restart wipes all conversation history.

**Improvement:** Swap `InMemorySaver` for a persistent checkpointer backed by a database. LangGraph supports [PostgreSQL and Redis checkpointers](https://langchain-ai.github.io/langgraph/concepts/persistence/) out of the box. This would:

- Survive backend restarts
- Allow users to return to a previous conversation
- Enable cross-device session resumption

Pair this with a `thread_id` tied to a user identity (see Auth in `deployment.md`) so threads are scoped to individual users rather than being anonymous.

---

## Ambiguous Ingredients

**Current state:** When a user says "I have some peppers," the graph proceeds assuming it knows what kind. This can produce recipes with the wrong heat level or flavor profile.

**Improvement:** Extend the `inquire` node (or add a dedicated `clarify_ingredients` node) to detect ambiguity in ingredient descriptions. Heuristics to flag:

- Generic produce names with many varieties (peppers, mushrooms, onions, greens)
- Quantities described as "some" or "a few" where precision matters
- Ingredient names that vary by region (e.g. "rocket" vs. "arugula")

The node would ask a targeted clarifying question before passing to `check_cookware` → `generate_recipe`. This keeps the existing interrupt/resume flow in `main.py` unchanged.

---

## Non-English Queries

**Current state:** Prompts are in English and the classify/inquire/generate nodes all assume English input.

**Improvement:** Add a lightweight language detection step before `classify`. If a non-English query is detected:

1. Translate it to English for internal graph processing (Claude handles this well with a simple system instruction)
2. Store the detected language in `AppState`
3. Translate the final response back to the user's language before returning

This keeps all graph logic language-agnostic while giving users a native-language experience. Alternatively, Claude can handle both translation and task completion in a single prompt — benchmark latency vs. a dedicated step.

---

## Unit Conversion (Metric / Imperial)

**Current state:** Recipes use whatever units the source material provides. Users may get cups and Fahrenheit when they expected grams and Celsius, or vice versa.

**Improvement:** Add a unit preference to the user profile (see User Preference Learning above) and apply a conversion pass when generating recipes. Options:

- **Prompt-level:** instruct `generate_recipe` to output in the preferred unit system — zero extra latency, but may be inconsistent
- **Post-processing tool:** add a `convert_units` tool the LLM can call after generating a recipe, applying precise conversions

A simpler short-term fix is to always output dual units (e.g. "200g / 7oz") in the recipe prompt instructions.

---

## Context Window & Automatic Summarization

**Current state:** Each LangGraph thread accumulates the full message history. Long multi-turn conversations will eventually exceed Claude's context window, causing silent truncation or errors.

**Improvement:** Add a summarization step that fires when the message list exceeds a token threshold. The approach:

1. After each graph run, count tokens in `state["messages"]`
2. If over the threshold (e.g. 80% of the model's context limit), invoke a summarization call that condenses older messages into a single `SystemMessage` summary
3. Replace the older messages with the summary, keeping only the most recent N turns verbatim

LangGraph's [memory guide](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/) documents this pattern. The `thread_id` in the checkpointer preserves continuity across this compaction.

---

## Tool Failures & Circuit Breaker

**Current state:** The `web_search` tool has no retry logic and no fallback. If Serper returns an error or rate-limits the request, the LLM receives a tool error and may hallucinate or produce a degraded response.

**Improvement:** Add resilience at two levels:

- **Retry with backoff:** wrap `web_search` in a retry decorator (e.g. `tenacity`) that retries transient errors 2–3 times before failing
- **Circuit breaker:** track consecutive failures; if the breaker is open, skip the tool call entirely and have the LLM answer from its training knowledge, with a note to the user that real-time info is unavailable
- **Fallback search provider:** if Serper is unavailable, fall back to another SERP API or a cached result

The LangGraph `ToolNode` can be subclassed to intercept errors before they propagate to the model.

---

## Thread Persistence After Backend Failure

**Current state:** `InMemorySaver` means any backend crash or restart drops all in-flight threads. Users mid-conversation lose their context entirely.

**Improvement:** This is partly addressed by the persistent checkpointer above, but also requires:

- A database to store the mapping of `thread_id` → user, so threads can be looked up after restart
- The frontend should store the `thread_id` in local storage and re-attach to the thread on reload
- A TTL or expiry policy for old threads to keep the database lean

---

## Recipe Caching

**Current state:** Every request invokes the full graph — classify → inquire → generate — even for queries that are functionally identical (e.g. "classic carbonara" asked by many users).

**Improvement:** Cache generated recipes keyed on a normalized query hash. A two-tier approach:

- **In-process LRU cache:** cache the top N recipes in memory, evicting least-recently-used entries. Good for popular/trending recipes with high hit rates
- **Distributed cache (Redis):** share the cache across multiple backend instances; necessary once the backend scales horizontally (see `deployment.md`)

Cache invalidation trigger: a time-based TTL (e.g. 24h) is sufficient for recipes. Don't cache responses that involved an `interrupt` (personalized to a specific user's answer).

---

## Recipe Quality Validation

**Current state:** Generated recipes are returned to the user as-is. There is no check that the output is safe, coherent, or culinarily sound.

**Improvement:** Add a lightweight validation pass after `generate_recipe`:

- **Safety check:** run the output through a classifier (Claude itself works well here with a simple prompt) to flag anything potentially harmful — dangerous food combinations, unsafe cooking temperatures, allergen-related issues
- **Structure check:** verify the response contains the expected sections (ingredients, instructions, timing) before returning; re-generate or prompt the user if missing
- **Hallucination heuristics:** flag implausibly large quantities or temperatures outside realistic ranges

This validation node would sit between `generate_recipe` and the final `response`, and could log flagged outputs to a moderation queue for human review.

---

## CI Pipeline

**Current state:** No automated checks run on pull requests or pushes.

**Improvement:** Add a GitHub Actions workflow that runs on every push and PR to `main`:

```
lint (ruff/eslint) → typecheck (mypy/tsc) → unit tests (pytest/jest) → build
```

Steps:
1. **Lint:** `ruff check` for backend, `eslint` for frontend
2. **Type check:** `mypy` for backend, `tsc --noEmit` for frontend
3. **Unit tests:** `pytest backend/` with mocked LLM calls (no real API keys needed)
4. **Docker build:** `docker compose build` to catch Dockerfile regressions
5. **Optional:** LangSmith dataset eval on a representative set of queries to catch prompt regressions

Block merges if any step fails. Use repository secrets for any API keys needed in integration tests.

---

## Prompt Versioning

**Current state:** Prompts are plain strings in `lib/prompts.py` with no history, no evaluation, and no way to roll back a regression.

**Improvement:**

- **Version in code:** add a version constant alongside each prompt (e.g. `CLASSIFY_PROMPT_V2`) and log which version was used in each request; this makes it possible to attribute quality changes to specific prompt edits in git history
- **LangSmith datasets:** define a golden set of (input, expected output) pairs per node; run evals on every prompt change to measure regression before merging
- **Feature flags:** allow deploying a new prompt version to a percentage of traffic before fully rolling it out, using a simple env var or a feature flag service

The combination of git history for diffs and LangSmith for eval results gives a clear audit trail for every prompt change.
