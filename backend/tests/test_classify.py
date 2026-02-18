from graphs.classify import classify, ClassificationResult


def test_classify_cooking_recipe_request(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = ClassificationResult(
        is_cooking_related=True, query_intent="recipe_request"
    )
    mocker.patch("graphs.classify.llm", mock_llm)

    result = classify({"query": "How do I make pasta carbonara?"})

    assert result["is_cooking_related"] is True
    assert result["query_intent"] == "recipe_request"


def test_classify_cooking_what_can_i_make(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = ClassificationResult(
        is_cooking_related=True, query_intent="what_can_i_make"
    )
    mocker.patch("graphs.classify.llm", mock_llm)

    result = classify({"query": "What can I make with eggs and spinach?"})

    assert result["is_cooking_related"] is True
    assert result["query_intent"] == "what_can_i_make"


def test_classify_cooking_general(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = ClassificationResult(
        is_cooking_related=True, query_intent="general"
    )
    mocker.patch("graphs.classify.llm", mock_llm)

    result = classify({"query": "What is the Maillard reaction?"})

    assert result["is_cooking_related"] is True
    assert result["query_intent"] == "general"


def test_classify_not_cooking(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = ClassificationResult(
        is_cooking_related=False, query_intent=None
    )
    mocker.patch("graphs.classify.llm", mock_llm)

    result = classify({"query": "What is the capital of France?"})

    assert result["is_cooking_related"] is False
    assert result["query_intent"] is None
