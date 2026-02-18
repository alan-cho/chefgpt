import logging

from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> str:
    """Search the web for up-to-date information about recipes, ingredients, or cooking techniques."""
    try:
        return _run_search(query)
    except Exception:
        return "Web search is currently unavailable. Please answer from your training knowledge."


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
def _run_search(query: str) -> str:
    try:
        search = GoogleSerperAPIWrapper()
        return search.run(query)
    except Exception as e:
        logger.error("web_search failed: %s", e)
        raise
