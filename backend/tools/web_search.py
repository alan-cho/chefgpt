from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper


@tool
def web_search(query: str) -> str:
    """Search the web for up-to-date information about recipes, ingredients, or cooking techniques."""
    search = GoogleSerperAPIWrapper()
    return search.run(query)
