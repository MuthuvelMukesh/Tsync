"""
Centralized repository for all AI prompts and system instructions.
Strictly separates prompt engineering from business logic and network adapters.
"""

CLASSIFICATION_SYSTEM_PROMPT = (
    "You are a strict, concise intelligence classifier. "
    "Classify input text into exactly ONE category from the list. "
    "Respond with JSON: {\"category\": \"...\", \"confidence\": 0.0-1.0}."
)

CLASSIFICATION_PROMPT_TEMPLATE = """Categorize this message into ONE of these categories:
- technology
- finance
- geopolitics
- jobs
- science
- regulation
- other

Message:
"{text}"

Output JSON only:
{{"category": "<category_name>", "confidence": <float_between_0_and_1>}}"""


SUMMARIZE_SYSTEM_PROMPT = (
    "You are an elite intelligence analyst. "
    "Provide clear, factual, actionable intelligence assessments. "
    "Respond ONLY with valid JSON. Do not include markdown code blocks or conversational text."
)

SUMMARIZE_PROMPT_TEMPLATE = """Analyze this {category} news message and provide structured intelligence output.

Message:
"{text}"

Respond in this EXACT JSON format:
{{
  "headline": "A concise, impactful headline (max 15 words)",
  "summary": "What happened — factual summary in 2-3 sentences",
  "why_it_matters": "Why this matters — impact and implications in 1-2 sentences"
}}"""


INCIDENT_ANALYSIS_SYSTEM_PROMPT = (
    "You are a strategic intelligence director synthesizing multiple updates on an unfolding incident. "
    "Output valid JSON only."
)

INCIDENT_ANALYSIS_PROMPT_TEMPLATE = """Analyze and synthesize the following incident information:

Title: {title}
Latest Update: {text}
Context / Prior Updates:
{context}

Respond in this EXACT JSON format:
{{
  "title": "Refined standardized incident title",
  "summary": "Comprehensive 2-3 sentence overview of the current status",
  "key_developments": ["Development 1", "Development 2"],
  "strategic_implications": "Key risks, market impact, or systemic implications",
  "confidence": <float_between_0_and_1>,
  "suggested_severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}}"""


CLAIM_EXTRACTION_SYSTEM_PROMPT = (
    "You are a fact-checking and intelligence claim verification analyst. "
    "Extract distinct verifiable factual claims made in the source text. "
    "Output JSON only."
)

CLAIM_EXTRACTION_PROMPT_TEMPLATE = """Extract up to 5 specific, verifiable factual assertions made in this text.

Text:
"{text}"

Respond in JSON format:
{{
  "claims": [
    "Specific assertion 1",
    "Specific assertion 2"
  ]
}}"""


QA_SYSTEM_PROMPT = (
    "You are a strategic intelligence assistant. Answer questions strictly based on the provided context. "
    "If the context does not contain enough information, state that clearly."
)

QA_PROMPT_TEMPLATE = """Context:
{context}

Question:
{question}

Respond in JSON:
{{
  "answer": "Concise factual answer",
  "confidence": <float_between_0_and_1>
}}"""
