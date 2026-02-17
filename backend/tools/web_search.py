from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper


@tool
def web_search(query: str) -> str:
    search = GoogleSerperAPIWrapper()
    return search.run(query)
