from typing import Annotated, TypedDict, Literal, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AppState(TypedDict):
    query: str
    query_intent: Optional[Literal["recipe_request", "what_can_i_make", "general"]]

    is_cooking_related: bool

    messages: Annotated[list[AnyMessage], add_messages]

    user_preferences: Optional[str]

    available_cookware: list[str]
    required_cookware: list[str]
    missing_cookware: list[str]

    response: str
