"""
Integration tests for OpenRouter AI provider adapter with mocked HTTP layer.
"""

from unittest.mock import patch
import httpx
import pytest

from app.ai.openrouter import OpenRouterAIProvider


@pytest.mark.asyncio
async def test_openrouter_classify_mocked():
    provider = OpenRouterAIProvider(api_key="mock_key")

    mock_resp = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {
                    "message": {
                        "content": '{"category": "technology", "confidence": 0.95}'
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp):
        res = await provider.classify("OpenAI releases model")
        assert res.category == "technology"
        assert res.confidence == 0.95


@pytest.mark.asyncio
async def test_openrouter_summarize_mocked():
    provider = OpenRouterAIProvider(api_key="mock_key")

    mock_resp = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {
                    "message": {
                        "content": (
                            '```json\n{\n'
                            '  "headline": "GPT-5 Released",\n'
                            '  "summary": "OpenAI announced GPT-5 today.",\n'
                            '  "why_it_matters": "Changes AI landscape."\n'
                            '}\n```'
                        )
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch.object(httpx.AsyncClient, "post", return_value=mock_resp):
        res = await provider.summarize("OpenAI announced GPT-5 today.", "technology")
        assert res.headline == "GPT-5 Released"
        assert res.summary == "OpenAI announced GPT-5 today."
        assert res.why_it_matters == "Changes AI landscape."
