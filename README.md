# ChefGPT

An AI cooking assistant that answers recipe questions, suggests ingredients, and explains techniques. Built with a FastAPI backend (LangGraph + Claude) and a Next.js frontend.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose, **or**
- Python 3.13+ and Node 20+ for local development

## Environment Setup

Copy the sample env file and fill in your API keys:

```bash
cp backend/.env.sample backend/.env
```

Then edit `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...   # Required — Claude API key
SERPER_API_KEY=...             # Required — web search (serper.dev)
DEBUG=false                    # Set to true to enable verbose backend logs
```

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `SERPER_API_KEY` | Search API key from [serper.dev](https://serper.dev) |
| `DEBUG` | `true` enables INFO-level logs; `false` (default) silences them |

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

## API

### `POST /query`

Send a question to the assistant.

**Request body:**

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | The user's question |
| `thread_id` | string | `null` | Conversation thread ID (returned on interrupt) |
| `resume` | string | `null` | Resume value after an interrupt |
| `stream` | boolean | `true` | Stream tokens via SSE |
| `debug` | boolean | `false` | Return per-node graph trace |

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

| `type` | Description |
|---|---|
| `token` | Partial text chunk (`content` field) |
| `interrupt` | Assistant needs more info (`question` and `thread_id` fields) |
| `response` | Final complete response (`content` field) |
| `done` | Stream finished |
