from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from graphs.generate_recipe import generate_recipe


async def test_no_prior_messages_builds_prompt(mocker):
    mock_response = AIMessage(content="Here is your recipe.")
    mock_llm = mocker.MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mocker.patch("graphs.generate_recipe.llm", mock_llm)

    state = {
        "query": "Make me pasta carbonara",
        "messages": [],
        "available_cookware": ["frying pan"],
        "missing_cookware": [],
        "user_preferences": None,
    }
    result = await generate_recipe(state)

    call_args = mock_llm.ainvoke.call_args[0][0]
    assert isinstance(call_args[0], SystemMessage)
    assert isinstance(call_args[1], HumanMessage)
    assert call_args[1].content == "Make me pasta carbonara"
    assert result["messages"] == [mock_response]


async def test_existing_messages_passed_through(mocker):
    existing_msg = AIMessage(content="Previous message")
    mock_response = AIMessage(content="Continued recipe.")
    mock_llm = mocker.MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mocker.patch("graphs.generate_recipe.llm", mock_llm)

    state = {
        "query": "Make me pasta carbonara",
        "messages": [existing_msg],
        "available_cookware": [],
        "missing_cookware": [],
        "user_preferences": None,
    }
    result = await generate_recipe(state)

    mock_llm.ainvoke.assert_called_once_with([existing_msg])
    assert result["messages"] == [mock_response]


async def test_response_with_tool_calls(mocker):
    tool_call = {
        "name": "web_search",
        "args": {"query": "carbonara recipe"},
        "id": "tc1",
    }
    mock_response = AIMessage(content="", tool_calls=[tool_call])
    mock_llm = mocker.MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mocker.patch("graphs.generate_recipe.llm", mock_llm)

    state = {
        "query": "Make me pasta carbonara",
        "messages": [],
        "available_cookware": [],
        "missing_cookware": [],
        "user_preferences": None,
    }
    result = await generate_recipe(state)

    assert len(result["messages"]) == 1
    assert len(result["messages"][0].tool_calls) == 1
    assert result["messages"][0].tool_calls[0]["name"] == "web_search"


async def test_response_without_tool_calls(mocker):
    mock_response = AIMessage(content="Here is a simple recipe.")
    mock_llm = mocker.MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mocker.patch("graphs.generate_recipe.llm", mock_llm)

    state = {
        "query": "Simple egg dish",
        "messages": [],
        "available_cookware": ["frying pan"],
        "missing_cookware": [],
        "user_preferences": None,
    }
    result = await generate_recipe(state)

    assert result["messages"][0].tool_calls == []
