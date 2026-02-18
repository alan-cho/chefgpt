from langchain_core.messages import AIMessage

from graphs.validate_recipe import validate_recipe, RecipeValidation


def test_valid_recipe_returns_empty(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = RecipeValidation(
        is_safe=True, is_well_structured=True, issues=[]
    )
    mocker.patch("graphs.validate_recipe.llm", mock_llm)

    msg = AIMessage(
        content="# Pasta Carbonara\n\n**Prep: 10min**\n\n## Ingredients\n- 200g pasta\n\n## Instructions\n1. Boil pasta."
    )
    result = validate_recipe({"messages": [msg]})

    assert result == {}
    mock_llm.invoke.assert_called_once()


def test_unsafe_recipe_returns_replacement_message(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = RecipeValidation(
        is_safe=False,
        is_well_structured=True,
        issues=["Recipe calls for undercooked chicken at 120°F"],
    )
    mocker.patch("graphs.validate_recipe.llm", mock_llm)

    msg = AIMessage(content="Cook chicken to 120°F for 5 minutes.")
    result = validate_recipe({"messages": [msg]})

    assert "messages" in result
    assert len(result["messages"]) == 1
    assert isinstance(result["messages"][0], AIMessage)
    assert "safe" in result["messages"][0].content.lower()


def test_safe_but_unstructured_recipe_passes_through(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = RecipeValidation(
        is_safe=True,
        is_well_structured=False,
        issues=["Missing timing information"],
    )
    mocker.patch("graphs.validate_recipe.llm", mock_llm)

    msg = AIMessage(content="Just mix stuff together and cook it.")
    result = validate_recipe({"messages": [msg]})

    assert result == {}


def test_empty_content_skips_llm(mocker):
    mock_llm = mocker.MagicMock()
    mocker.patch("graphs.validate_recipe.llm", mock_llm)

    msg = AIMessage(content="")
    result = validate_recipe({"messages": [msg]})

    assert result == {}
    mock_llm.invoke.assert_not_called()
