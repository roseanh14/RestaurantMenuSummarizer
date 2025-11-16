from main import normalize_prices_tool


def test_normalize_prices_basic():
    raw = ["145,-", "199 Kč", "250czk"]
    result = normalize_prices_tool(raw)
    assert result["normalized"] == [145.0, 199.0, 250.0]


def test_normalize_prices_invalid_and_none():
    raw = [None, "abc", "0", "12,5"]
    result = normalize_prices_tool(raw)
    assert result["normalized"] == [None, None, 0.0, 12.5]
