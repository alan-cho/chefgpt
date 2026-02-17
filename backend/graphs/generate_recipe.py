from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from backend.schemas.app_state import AppState
from tools.web_search import web_search
from lib.prompts import RECIPE_PROMPT

tools = [web_search]
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").bind_tools(tools)


def generate_recipe(state: AppState) -> AppState:
    if not state.get("messages"):
        messages = [
            SystemMessage(content=RECIPE_PROMPT),
            HumanMessage(content=state["query"]),
        ]
    else:
        messages = state["messages"]

    response = llm.invoke(messages)
    return {"messages": [response]}
