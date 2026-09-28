"""
Unit tests for confidence calculator.
"""

from app.intelligence.confidence import ConfidenceCalculator


def test_confidence_increases_with_sources():
    calc = ConfidenceCalculator()
    conf_1 = calc.calculate_incident_confidence(["channel_1"], 1, 0)
    conf_mult = calc.calculate_incident_confidence(["channel_1", "channel_2", "channel_3", "channel_4"], 4, 0)
    assert conf_mult > conf_1


def test_confidence_penalized_by_contradictions():
    calc = ConfidenceCalculator()
    clean_conf = calc.calculate_incident_confidence(["c1", "c2"], 2, 0)
    disputed_conf = calc.calculate_incident_confidence(["c1", "c2"], 2, 2)
    assert disputed_conf < clean_conf
