import json

from dotenv import load_dotenv

load_dotenv()

from uuid import uuid4  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402
from langgraph.types import Command  # noqa: E402

from lib.logging import serialize, get_logger  # noqa: E402
from schemas.query import Query  # noqa: E402
from graphs.graph import graph  # noqa: E402

logger = get_logger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _has_interrupt(state) -> str | None:
    """Check if the graph state contains an interrupt and return the question."""
    tasks = state.tasks
    for task in tasks:
        if task.interrupts:
            return task.interrupts[0].value
    return None


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


STREAMING_NODES = {"assistant", "generate_recipe"}


def _text_content(content) -> str:
    """Extract plain text from an AIMessage content field.

    Content can be a string or a list of content blocks like
    [{'type': 'text', 'text': '...'}, {'type': 'tool_use', ...}].
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return str(content)


@app.post("/query")
async def query(request: Query):
    thread_id = request.thread_id or str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    is_resume = request.resume is not None and request.thread_id is not None

    if is_resume:
        graph_input = Command(resume=request.resume)
    else:
        graph_input = {"query": request.query}

    if request.stream:

        async def event_stream():
            async for chunk, metadata in graph.astream(
                graph_input, config, stream_mode="messages"
            ):
                node = metadata.get("langgraph_node")
                text = _text_content(chunk.content)
                if node in STREAMING_NODES and text:
                    yield _sse({"type": "token", "content": text})

            graph_state = graph.get_state(config)
            interrupt_question = _has_interrupt(graph_state)
            if interrupt_question:
                yield _sse(
                    {
                        "type": "interrupt",
                        "question": interrupt_question,
                        "thread_id": thread_id,
                    }
                )
            elif graph_state.values.get("response"):
                yield _sse(
                    {"type": "response", "content": graph_state.values["response"]}
                )
            elif graph_state.values.get("messages"):
                yield _sse(
                    {
                        "type": "response",
                        "content": _text_content(
                            graph_state.values["messages"][-1].content
                        ),
                    }
                )

            yield _sse({"type": "done"})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    if not request.debug:
        state = await graph.ainvoke(graph_input, config)

        graph_state = graph.get_state(config)
        interrupt_question = _has_interrupt(graph_state)
        if interrupt_question:
            return {
                "type": "interrupt",
                "question": interrupt_question,
                "thread_id": thread_id,
            }

        if state.get("response"):
            return {"type": "response", "response": state["response"]}

        return {
            "type": "response",
            "response": _text_content(state["messages"][-1].content),
        }

    nodes = []
    final_state = {}

    async for chunk in graph.astream(graph_input, config, stream_mode="updates"):
        for node_name, delta in chunk.items():
            if delta is not None:
                nodes.append({"node": node_name, "delta": serialize(delta)})
                final_state.update(delta)

    graph_state = graph.get_state(config)
    interrupt_question = _has_interrupt(graph_state)
    if interrupt_question:
        return {
            "type": "interrupt",
            "question": interrupt_question,
            "thread_id": thread_id,
            "debug": {
                "nodes": nodes,
                "state": serialize(final_state),
            },
        }

    response = final_state.get("response") or _text_content(
        final_state.get("messages", [{}])[-1].content
    )

    return {
        "type": "response",
        "response": response,
        "debug": {
            "nodes": nodes,
            "state": serialize(final_state),
        },
    }
