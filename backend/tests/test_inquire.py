from graphs.inquire import inquire, ClarifyingQuestion


def test_inquire_no_clarification_needed(mocker):
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = ClarifyingQuestion(
        needs_clarification=False, question=None
    )
    mocker.patch("graphs.inquire.llm", mock_llm)
    mock_interrupt = mocker.patch("graphs.inquire.interrupt")

    result = inquire({"query": "Make me a pasta dish"})

    assert result == {}
    mock_interrupt.assert_not_called()


def test_inquire_needs_clarification(mocker):
    question = "Do you have any dietary restrictions?"
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = ClarifyingQuestion(
        needs_clarification=True, question=question
    )
    mocker.patch("graphs.inquire.llm", mock_llm)
    mock_interrupt = mocker.patch(
        "graphs.inquire.interrupt", return_value="No restrictions"
    )

    result = inquire({"query": "Make me something good"})

    mock_interrupt.assert_called_once_with(question)
    assert result == {"user_preferences": "No restrictions"}
