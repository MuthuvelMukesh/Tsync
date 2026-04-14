"""
ai_processor.py — AI-powered processing via OpenRouter API.

Used ONLY as a fallback when rule-based processing is insufficient.
Handles categorization, headline generation, and summary creation.
Designed for minimal API usage (freemium optimization).
"""

import os
import json
import time
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Use a cost-effective model
DEFAULT_MODEL = "google/gemini-2.0-flash-001"

# Rate limiting
_last_call_time = 0
MIN_CALL_INTERVAL = 1.5  # seconds between API calls


def _rate_limit():
    """Enforce minimum interval between API calls."""
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


def _call_openrouter(
    prompt: str,
    system_prompt: str = "",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 300,
) -> Optional[str]:
    """
    Make a single call to OpenRouter API.

    Returns response text or None on failure.
    """
    if not OPENROUTER_API_KEY:
        print("[AI] ERROR: OPENROUTER_API_KEY not set in .env")
        return None

    _rate_limit()

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/tsync",
        "X-Title": "Tsync Intelligence Engine",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"[AI] API error: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"[AI] Response parse error: {e}")
        return None


def ai_categorize(text: str) -> Optional[str]:
    """
    Categorize a message using AI when rules fail.

    Returns category string or None.
    """
    prompt = f"""Categorize this message into ONE of these categories:
- technology
- finance
- geopolitics
- jobs
- science
- regulation
- other

Message: "{text[:500]}"

Respond with ONLY the category name, nothing else."""

    result = _call_openrouter(prompt, max_tokens=20)
    if result:
        category = result.strip().lower().replace('"', "").replace(".", "")
        valid = {
            "technology", "finance", "geopolitics",
            "jobs", "science", "regulation", "other",
        }
        return category if category in valid else "other"
    return None


def ai_generate_intelligence(text: str, category: str) -> Optional[dict]:
    """
    Generate headline, summary (What), and impact (Why) for a message.

    This is the ONLY expensive AI call and is used ONLY for
    selected high-value messages.

    Returns dict with headline, summary, why_it_matters or None.
    """
    prompt = f"""Analyze this {category} news message and provide intelligence output.

Message: "{text[:800]}"

Respond in this EXACT JSON format (no markdown, no code blocks):
{{
  "headline": "A concise, impactful headline (max 15 words)",
  "summary": "What happened — factual summary in 2-3 sentences",
  "why_it_matters": "Why this matters — impact and implications in 1-2 sentences"
}}"""

    system = (
        "You are a concise intelligence analyst. "
        "Output valid JSON only. No markdown formatting."
    )

    result = _call_openrouter(prompt, system_prompt=system, max_tokens=250)

    if not result:
        return None

    try:
        # Strip any markdown code blocks if present
        clean = result.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        parsed = json.loads(clean)
        return {
            "headline": parsed.get("headline", ""),
            "summary": parsed.get("summary", ""),
            "why_it_matters": parsed.get("why_it_matters", ""),
        }
    except json.JSONDecodeError:
        print(f"[AI] Failed to parse JSON response: {result[:100]}")
        return None


def batch_generate_intelligence(messages: list[dict]) -> list[dict]:
    """
    Generate intelligence for a batch of selected messages.

    Only processes messages that don't already have headlines.
    """
    processed = 0
    total = len(messages)

    for i, msg in enumerate(messages):
        if msg.get("headline"):
            continue

        print(f"[AI] Generating intelligence {i+1}/{total}...")

        result = ai_generate_intelligence(
            msg["text"], msg.get("category", "unknown")
        )

        if result:
            msg["headline"] = result["headline"]
            msg["summary"] = result["summary"]
            msg["why_it_matters"] = result["why_it_matters"]
            processed += 1
        else:
            # Fallback: use first line as headline, truncated text as summary
            lines = msg["text"].split("\n")
            msg["headline"] = lines[0][:80] + ("..." if len(lines[0]) > 80 else "")
            msg["summary"] = msg["text"][:200] + "..."
            msg["why_it_matters"] = "Analysis unavailable."

    print(f"[AI] Generated intelligence for {processed}/{total} messages")
    return messages
