"""
Unit tests for text normalization and similarity utilities.
"""

from app.processing.normalization import (
    clean_text,
    compute_jaccard_similarity,
    generate_content_hash,
    strip_urls,
)


def test_strip_urls():
    text = "Read more at https://example.com/news?id=42 or www.reuters.com today."
    cleaned = strip_urls(text)
    assert "https://" not in cleaned
    assert "www.reuters.com" not in cleaned


def test_clean_text():
    raw = "Headline   with   excessive\t spaces and \n\n\n\nnewlines."
    cleaned = clean_text(raw)
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned


def test_content_hash():
    h1 = generate_content_hash("OpenAI announces GPT-5.")
    h2 = generate_content_hash("openai announces gpt-5!")
    assert h1 == h2


def test_jaccard_similarity():
    t1 = "OpenAI announced groundbreaking GPT-5 model today"
    t2 = "OpenAI releases groundbreaking GPT-5 architecture"
    sim = compute_jaccard_similarity(t1, t2)
    assert sim >= 0.35

    t3 = "Completely different topic regarding agricultural fertilizer supplies"
    assert compute_jaccard_similarity(t1, t3) == 0.0
