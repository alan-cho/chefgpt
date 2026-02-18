from graphs.check_cookware import check_cookware, CookwareRequirement


def test_all_cookware_available(mocker):
    # "frying pan" and "spatula" are both in USER_COOKWARE (lowercased)
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = CookwareRequirement(
        required_cookware=["Frying Pan", "Spatula"]
    )
    mocker.patch("graphs.check_cookware.llm", mock_llm)

    result = check_cookware({"query": "Fry some eggs"})

    assert result["required_cookware"] == ["Frying Pan", "Spatula"]
    assert set(result["available_cookware"]) == {"frying pan", "spatula"}
    assert result["missing_cookware"] == []


def test_mixed_cookware_availability(mocker):
    # "frying pan" in USER_COOKWARE, "oven" is not
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = CookwareRequirement(
        required_cookware=["Frying Pan", "Oven"]
    )
    mocker.patch("graphs.check_cookware.llm", mock_llm)

    result = check_cookware({"query": "Make roasted chicken"})

    assert result["required_cookware"] == ["Frying Pan", "Oven"]
    assert result["available_cookware"] == ["frying pan"]
    assert result["missing_cookware"] == ["oven"]


def test_all_cookware_missing(mocker):
    # Neither "oven" nor "microwave" are in USER_COOKWARE
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = CookwareRequirement(
        required_cookware=["Oven", "Microwave"]
    )
    mocker.patch("graphs.check_cookware.llm", mock_llm)

    result = check_cookware({"query": "Bake a cake"})

    assert result["required_cookware"] == ["Oven", "Microwave"]
    assert result["available_cookware"] == []
    assert set(result["missing_cookware"]) == {"oven", "microwave"}
