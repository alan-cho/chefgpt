from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from lib.logging import get_logger
from schemas.app_state import AppState
from tools.web_search import web_search
from lib.prompts import build_recipe_system_prompt

logger = get_logger(__name__)

tools = [web_search]
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").bind_tools(tools)


def generate_recipe(state: AppState) -> AppState:
    if not state.get("messages"):
        system_prompt = build_recipe_system_prompt(state)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["query"]),
        ]
    else:
        messages = state["messages"]

    response = llm.invoke(messages)
    if response.tool_calls:
        for tc in response.tool_calls:
            logger.info("[tool_call] %s | args=%s", tc["name"], tc.get("args", {}))
    return {"messages": [response]}
