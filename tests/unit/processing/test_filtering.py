"""
Unit tests for filtering engine.
"""

from datetime import datetime, timezone
from app.domain.messages import RawMessage
from app.processing.filtering import filter_raw_message, is_spam, is_too_short


def test_is_spam():
    spam_msg = "Join our telegram group for 100% guaranteed crypto profit! Click here now!"
    assert is_spam(spam_msg)

    legit_msg = "Federal Reserve decided to hold interest rates steady following CPI release."
    assert not is_spam(legit_msg)


def test_is_too_short():
    assert is_too_short("hello", min_length=30)
    assert not is_too_short("This is a sufficiently long message detailing important economic events.", min_length=30)


def test_filter_raw_message():
    now = datetime.now(timezone.utc)
    spam_raw = RawMessage("c", "1", "Free money giveaway! DM me now!", now)
    res_spam = filter_raw_message(spam_raw)
    assert res_spam.should_skip
    assert res_spam.reason == "spam"

    legit_raw = RawMessage(
        "c", "2",
        "European Commission announced new antitrust investigations into major cloud providers.",
        now,
    )
    res_legit = filter_raw_message(legit_raw)
    assert not res_legit.should_skip
