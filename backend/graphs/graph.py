from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from graphs.generate_recipe import generate_recipe
from graphs.generate_recipe import tools as recipe_tools
from schemas.app_state import AppState


def should_continue(state: AppState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


tool_node = ToolNode(recipe_tools)

graph = (
    StateGraph(AppState)
    .add_node("generate_recipe", generate_recipe)
    .add_node("tools", tool_node)
    .set_entry_point("generate_recipe")
    .add_conditional_edges("generate_recipe", should_continue)
    .add_edge("tools", "generate_recipe")
    .compile()
)
