"""
Unit tests verifying prompts formatting.
"""

from app.intelligence.prompts import (
    CLASSIFICATION_PROMPT_TEMPLATE,
    SUMMARIZE_PROMPT_TEMPLATE,
    INCIDENT_ANALYSIS_PROMPT_TEMPLATE,
    CLAIM_EXTRACTION_PROMPT_TEMPLATE,
    QA_PROMPT_TEMPLATE,
)


def test_prompts_formatting():
    p1 = CLASSIFICATION_PROMPT_TEMPLATE.format(text="test text")
    assert "test text" in p1

    p2 = SUMMARIZE_PROMPT_TEMPLATE.format(category="finance", text="test text")
    assert "finance" in p2

    p3 = INCIDENT_ANALYSIS_PROMPT_TEMPLATE.format(title="T", text="msg", context="ctx")
    assert "Title: T" in p3

    p4 = CLAIM_EXTRACTION_PROMPT_TEMPLATE.format(text="claim text")
    assert "claim text" in p4

    p5 = QA_PROMPT_TEMPLATE.format(question="what?", context="ctx")
    assert "what?" in p5
