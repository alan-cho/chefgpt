import logging
import os


DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


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
