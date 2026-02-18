from langchain_core.messages import AIMessage
from langgraph.graph import END

from graphs.graph import (
    route_after_classify,
    route_after_assistant,
    route_after_generate_recipe,
    route_after_tools,
)


# ---------------------------------------------------------------------------
# route_after_classify
# ---------------------------------------------------------------------------

def test_route_classify_not_cooking():
    state = {"is_cooking_related": False, "query_intent": None}
    assert route_after_classify(state) == "respond_not_cooking"


def test_route_classify_recipe_request():
    state = {"is_cooking_related": True, "query_intent": "recipe_request"}
    assert route_after_classify(state) == "inquire"


def test_route_classify_what_can_i_make():
    state = {"is_cooking_related": True, "query_intent": "what_can_i_make"}
    assert route_after_classify(state) == "inquire"


def test_route_classify_general():
    state = {"is_cooking_related": True, "query_intent": "general"}
    assert route_after_classify(state) == "assistant"


# ---------------------------------------------------------------------------
# route_after_assistant
# ---------------------------------------------------------------------------

def test_route_assistant_with_tool_calls():
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "web_search", "args": {"query": "pasta"}, "id": "1"}],
    )
    state = {"messages": [msg]}
    assert route_after_assistant(state) == "tools"


def test_route_assistant_no_tool_calls():
    msg = AIMessage(content="Here is some info.")
    state = {"messages": [msg]}
    assert route_after_assistant(state) == END


# ---------------------------------------------------------------------------
# route_after_generate_recipe
# ---------------------------------------------------------------------------

def test_route_generate_recipe_with_tool_calls():
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "web_search", "args": {"query": "lasagne"}, "id": "2"}],
    )
    state = {"messages": [msg]}
    assert route_after_generate_recipe(state) == "tools"


def test_route_generate_recipe_no_tool_calls():
    msg = AIMessage(content="Here is your recipe.")
    state = {"messages": [msg]}
    assert route_after_generate_recipe(state) == END


# ---------------------------------------------------------------------------
# route_after_tools
# ---------------------------------------------------------------------------

def test_route_tools_recipe_request():
    state = {"query_intent": "recipe_request"}
    assert route_after_tools(state) == "generate_recipe"


def test_route_tools_what_can_i_make():
    state = {"query_intent": "what_can_i_make"}
    assert route_after_tools(state) == "generate_recipe"


def test_route_tools_general():
    state = {"query_intent": "general"}
    assert route_after_tools(state) == "assistant"
