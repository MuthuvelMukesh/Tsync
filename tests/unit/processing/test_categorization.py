"""
Unit tests for rule-based categorization.
"""

from app.processing.categorization import categorize_by_rules


def test_categorize_technology():
    text = "NVIDIA announced a new Blackwell GPU architecture for artificial intelligence training."
    cat, conf = categorize_by_rules(text)
    assert cat == "technology"
    assert conf >= 0.5


def test_categorize_finance():
    text = "Federal Reserve decided to cut interest rates as inflation trends downward across bond markets."
    cat, conf = categorize_by_rules(text)
    assert cat == "finance"
    assert conf >= 0.5


def test_categorize_geopolitics():
    text = "NATO allies sign defense treaty regarding missile defense territory and border security."
    cat, conf = categorize_by_rules(text)
    assert cat == "geopolitics"
    assert conf >= 0.5


def test_categorize_science():
    text = "NASA discovered organic carbon molecules on Mars with Perseverance rover telescope."
    cat, conf = categorize_by_rules(text)
    assert cat == "science"
    assert conf >= 0.5


def test_categorize_unmatched():
    text = "A simple generic sentence with no specific domain keywords."
    cat, conf = categorize_by_rules(text)
    assert cat == "other"
    assert conf <= 0.3
