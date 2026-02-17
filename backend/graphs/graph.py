from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from graphs.classify import classify
from graphs.check_cookware import check_cookware
from graphs.generate_recipe import generate_recipe
from graphs.generate_recipe import tools as recipe_tools
from graphs.inquire import inquire
from lib.prompts import ASSISTANT_SYSTEM_PROMPT, NOT_COOKING_RESPONSE
from schemas.app_state import AppState
from tools.web_search import web_search


tools = [web_search]
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").bind_tools(tools)


def assistant(state: AppState) -> AppState:
    if not state.get("messages"):
        messages = [
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=state["query"]),
        ]
    else:
        messages = state["messages"]

    response = llm.invoke(messages)
    return {"messages": [response]}


def respond_not_cooking(state: AppState) -> AppState:
    return {"response": NOT_COOKING_RESPONSE}


def route_after_classify(state: AppState) -> str:
    if not state.get("is_cooking_related"):
        return "respond_not_cooking"
    intent = state.get("query_intent")
    if intent == "what_can_i_make":
        return "inquire"
    if intent == "recipe_request":
        return "check_cookware"
    return "assistant"


def route_after_assistant(state: AppState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def route_after_generate_recipe(state: AppState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def route_after_tools(state: AppState) -> str:
    intent = state.get("query_intent")
    if intent in ("recipe_request", "what_can_i_make"):
        return "generate_recipe"
    return "assistant"


all_tools = list({t.name: t for t in tools + recipe_tools}.values())

builder = StateGraph(AppState)

builder.add_node("classify", classify)
builder.add_node("assistant", assistant)
builder.add_node("inquire", inquire)
builder.add_node("check_cookware", check_cookware)
builder.add_node("generate_recipe", generate_recipe)
builder.add_node("respond_not_cooking", respond_not_cooking)
builder.add_node("tools", ToolNode(all_tools))

builder.set_entry_point("classify")
builder.add_conditional_edges("classify", route_after_classify)
builder.add_conditional_edges("assistant", route_after_assistant)
builder.add_edge("inquire", "check_cookware")
builder.add_edge("check_cookware", "generate_recipe")
builder.add_conditional_edges("generate_recipe", route_after_generate_recipe)
builder.add_conditional_edges("tools", route_after_tools)
builder.add_edge("respond_not_cooking", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
