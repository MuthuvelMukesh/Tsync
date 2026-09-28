"""
OpenRouter API implementation of the AIProvider protocol.
Uses httpx for asynchronous HTTP calls with retries, rate limiting, and structured response parsing.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional
import httpx

from app.ai.base import AIProvider, AIProviderError, RateLimitError
from app.ai.models import (
    ClassificationResult,
    SummaryResult,
    IncidentAnalysisResult,
    ClaimExtractionResult,
    QAResult,
)
from app.ai.retry import async_retry
from app.intelligence.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    CLASSIFICATION_PROMPT_TEMPLATE,
    SUMMARIZE_SYSTEM_PROMPT,
    SUMMARIZE_PROMPT_TEMPLATE,
    INCIDENT_ANALYSIS_SYSTEM_PROMPT,
    INCIDENT_ANALYSIS_PROMPT_TEMPLATE,
    CLAIM_EXTRACTION_SYSTEM_PROMPT,
    CLAIM_EXTRACTION_PROMPT_TEMPLATE,
    QA_SYSTEM_PROMPT,
    QA_PROMPT_TEMPLATE,
)


class OpenRouterAIProvider:
    """Async OpenRouter API client satisfying the AIProvider protocol."""

    def __init__(
        self,
        api_key: str,
        model: str = "google/gemini-2.0-flash-001",
        base_url: str = "https://openrouter.ai/api/v1",
        min_call_interval: float = 1.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.min_call_interval = min_call_interval
        self._last_call_time: float = 0.0
        self._lock = asyncio.Lock()

    async def _rate_limit(self) -> None:
        """Enforce spacing between calls to stay within free/standard tier limits."""
        async with self._lock:
            elapsed = time.time() - self._last_call_time
            if elapsed < self.min_call_interval:
                await asyncio.sleep(self.min_call_interval - elapsed)
            self._last_call_time = time.time()

    @staticmethod
    def _clean_json_text(text: str) -> str:
        """Strip markdown code fences if model returned them."""
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean = "\n".join(lines).strip()
        return clean

    @async_retry(max_retries=3, base_delay=1.5, exceptions=(httpx.HTTPError, RateLimitError))
    async def _call_api(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 500,
        temperature: float = 0.2,
    ) -> str:
        """Send chat completion request to OpenRouter."""
        if not self.api_key:
            raise AIProviderError("OpenRouter API key is not configured")

        await self._rate_limit()

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/MuthuvelMukesh/Tsync",
            "X-Title": "Tsync Modular Intelligence Engine",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 429:
                raise RateLimitError("OpenRouter rate limit reached (HTTP 429)")
            if resp.is_error:
                raise AIProviderError(f"OpenRouter HTTP error {resp.status_code}: {resp.text}")

            data = resp.json()
            try:
                content = data["choices"][0]["message"]["content"]
                return content.strip()
            except (KeyError, IndexError) as err:
                raise AIProviderError(f"Unexpected response structure from OpenRouter: {err}")

    async def classify(self, text: str) -> ClassificationResult:
        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(text=text[:800])
        try:
            raw = await self._call_api(
                prompt=prompt,
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                max_tokens=60,
            )
            clean = self._clean_json_text(raw)
            data = json.loads(clean)
            return ClassificationResult(
                category=data.get("category", "other").lower().strip(),
                confidence=float(data.get("confidence", 0.7)),
            )
        except Exception:
            # Fallback heuristic if JSON parse fails
            return ClassificationResult(category="other", confidence=0.5)

    async def summarize(self, text: str, category: str) -> SummaryResult:
        prompt = SUMMARIZE_PROMPT_TEMPLATE.format(category=category, text=text[:1200])
        try:
            raw = await self._call_api(
                prompt=prompt,
                system_prompt=SUMMARIZE_SYSTEM_PROMPT,
                max_tokens=300,
            )
            clean = self._clean_json_text(raw)
            data = json.loads(clean)
            return SummaryResult(
                headline=data.get("headline", text[:80] + "..."),
                summary=data.get("summary", text[:250] + "..."),
                why_it_matters=data.get("why_it_matters", "Analysis not provided."),
            )
        except Exception as e:
            # Fallback to local truncation
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            headline = lines[0][:80] if lines else "Update"
            return SummaryResult(
                headline=headline,
                summary=text[:250] + "...",
                why_it_matters="Automated summary fallback.",
            )

    async def analyze_incident(
        self, title: str, text: str, context: str = ""
    ) -> IncidentAnalysisResult:
        prompt = INCIDENT_ANALYSIS_PROMPT_TEMPLATE.format(
            title=title, text=text[:1000], context=context[:1500]
        )
        try:
            raw = await self._call_api(
                prompt=prompt,
                system_prompt=INCIDENT_ANALYSIS_SYSTEM_PROMPT,
                max_tokens=600,
            )
            clean = self._clean_json_text(raw)
            data = json.loads(clean)
            return IncidentAnalysisResult(
                title=data.get("title", title),
                summary=data.get("summary", ""),
                key_developments=data.get("key_developments", []),
                strategic_implications=data.get("strategic_implications", ""),
                confidence=float(data.get("confidence", 0.7)),
                suggested_severity=data.get("suggested_severity", "MEDIUM"),
            )
        except Exception:
            return IncidentAnalysisResult(
                title=title,
                summary=text[:300],
                key_developments=[text[:150]],
                strategic_implications="Standard incident development.",
                confidence=0.5,
                suggested_severity="LOW",
            )

    async def extract_claims(self, text: str) -> ClaimExtractionResult:
        prompt = CLAIM_EXTRACTION_PROMPT_TEMPLATE.format(text=text[:1000])
        try:
            raw = await self._call_api(
                prompt=prompt,
                system_prompt=CLAIM_EXTRACTION_SYSTEM_PROMPT,
                max_tokens=300,
            )
            clean = self._clean_json_text(raw)
            data = json.loads(clean)
            claims = data.get("claims", [])
            return ClaimExtractionResult(claims=claims)
        except Exception:
            return ClaimExtractionResult(claims=[])

    async def answer_question(self, question: str, context: str) -> QAResult:
        prompt = QA_PROMPT_TEMPLATE.format(question=question, context=context[:2000])
        try:
            raw = await self._call_api(
                prompt=prompt,
                system_prompt=QA_SYSTEM_PROMPT,
                max_tokens=400,
            )
            clean = self._clean_json_text(raw)
            data = json.loads(clean)
            return QAResult(
                answer=data.get("answer", "No answer could be determined from context."),
                confidence=float(data.get("confidence", 0.6)),
            )
        except Exception:
            return QAResult(answer="Unable to process question at this time.", confidence=0.0)
