import logging
import os
from functools import wraps
from typing import Callable


DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


_graph_logger = get_logger("graph")


def log_node(name: str) -> Callable:
    """Wrap a graph node with entry/exit logging and automatic tool call detection."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(state):
            _graph_logger.info("[node:%s] entering", name)
            result = fn(state)
            if result:
                msgs = result.get("messages", [])
                if msgs:
                    last = msgs[-1]
                    if hasattr(last, "tool_calls") and last.tool_calls:
                        for tc in last.tool_calls:
                            _graph_logger.info(
                                "[tool_call] %s | args=%s",
                                tc["name"],
                                tc.get("args", {}),
                            )
                _graph_logger.info(
                    "[node:%s] exiting | keys=%s", name, list(result.keys())
                )
            else:
                _graph_logger.info("[node:%s] exiting | no state changes", name)
            return result

        return wrapper

    return decorator


def serialize(obj):
    """Convert LangChain objects to JSON-serializable dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, list):
        return [serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    return obj
