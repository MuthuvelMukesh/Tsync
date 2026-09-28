"""
Unit tests for importance scoring.
"""

from app.processing.scoring import score_message


def test_score_breaking_high_impact():
    text = (
        "BREAKING: Critical zero-day vulnerability discovered in global cloud infrastructure. "
        "Over $10 billion in damage reported as major financial institutions shut down systems."
    )
    score = score_message(text, category="technology")
    assert score >= 7.5


def test_score_routine_message():
    text = "Here is a standard minor update on company office hours."
    score = score_message(text, category="other")
    assert score <= 4.0


def test_score_bounded():
    score = score_message("A" * 500, category="geopolitics")
    assert 0.0 <= score <= 10.0
