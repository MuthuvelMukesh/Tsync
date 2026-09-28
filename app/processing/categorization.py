"""
Rule-based categorization engine.
Extracts category signals based on curated keyword hierarchies without calling AI APIs.
"""

from typing import Dict, Tuple

CATEGORY_RULES: Dict[str, Dict[str, list[str]]] = {
    "technology": {
        "primary": [
            "AI", "artificial intelligence", "machine learning", "GPT",
            "LLM", "neural network", "deep learning", "blockchain",
            "cryptocurrency", "bitcoin", "ethereum", "software",
            "open source", "github", "API", "cloud computing",
            "cybersecurity", "data breach", "hack", "vulnerability",
            "5G", "quantum", "robotics", "semiconductor", "chip",
            "startup", "tech company", "silicon valley", "NVIDIA",
            "Google", "Microsoft", "Apple", "Meta", "OpenAI",
            "Amazon Web Services", "AWS", "Azure", "GPU",
        ],
        "secondary": [
            "app", "update", "release", "platform", "digital",
            "server", "database", "code", "developer", "launch",
            "model", "training", "compute", "algorithm",
        ],
    },
    "finance": {
        "primary": [
            "stock market", "S&P 500", "NASDAQ", "Dow Jones",
            "interest rate", "Federal Reserve", "inflation",
            "GDP", "recession", "IPO", "earnings", "revenue",
            "investment", "hedge fund", "venture capital",
            "bond", "treasury", "forex", "commodity",
            "banking", "fintech", "central bank", "monetary policy",
            "fiscal", "bull market", "bear market", "crypto market",
        ],
        "secondary": [
            "market", "price", "fund", "trading", "financial",
            "economy", "profit", "loss", "valuation", "growth",
            "shares", "equity", "capital", "budget",
        ],
    },
    "geopolitics": {
        "primary": [
            "sanctions", "NATO", "United Nations", "UN",
            "diplomacy", "treaty", "war", "conflict",
            "military", "nuclear", "missile", "invasion",
            "coup", "election", "regime", "alliance",
            "territory", "border", "geopolitical",
            "foreign policy", "embassy", "summit",
        ],
        "secondary": [
            "government", "president", "minister", "country",
            "nation", "political", "defense", "security",
            "intelligence", "cooperation", "dispute",
        ],
    },
    "jobs": {
        "primary": [
            "hiring", "layoff", "layoffs", "job opening",
            "recruitment", "remote work", "salary", "resume",
            "interview", "career", "unemployment",
            "workforce", "talent", "job market",
            "mass layoff", "downsizing", "restructuring",
        ],
        "secondary": [
            "employee", "position", "role", "team",
            "company", "work", "office", "job",
        ],
    },
    "science": {
        "primary": [
            "research", "study", "discovery", "scientific", "scientist", "scientists",
            "NASA", "SpaceX", "space", "climate change", "Mars", "rover", "satellite",
            "spacecraft", "orbit", "genome", "CRISPR", "vaccine", "clinical trial",
            "physics", "biology", "chemistry", "astronomy",
            "planet", "telescope", "fossil", "species",
        ],
        "secondary": [
            "experiment", "lab", "university", "professor",
            "journal", "published", "findings", "evidence",
        ],
    },
    "regulation": {
        "primary": [
            "regulation", "legislation", "bill", "law",
            "compliance", "SEC", "FTC", "EU regulation",
            "GDPR", "antitrust", "monopoly", "ban",
            "policy", "executive order", "legal",
        ],
        "secondary": [
            "rule", "enforce", "court", "ruling", "judge",
            "penalty", "fine", "approval",
        ],
    },
}


import re

def _matches_keyword(kw: str, text_lower: str, text_upper: str) -> bool:
    """Match keyword respecting word boundaries for acronyms and short terms."""
    if len(kw) <= 3:
        # Strict boundary for short acronyms like AI, UN, 5G, GDP, SEC, FED
        pattern = rf"\b{re.escape(kw.lower())}\b"
        return bool(re.search(pattern, text_lower))
    return kw.lower() in text_lower


def categorize_by_rules(text: str) -> Tuple[str, float]:
    """
    Attempt rule-based categorization using keyword weights.
    Returns (category, confidence).
    """
    text_lower = text.lower()
    text_upper = text.upper()
    scores: Dict[str, float] = {}

    for category, kw_groups in CATEGORY_RULES.items():
        score = 0.0
        for kw in kw_groups["primary"]:
            if _matches_keyword(kw, text_lower, text_upper):
                score += 2.0
        for kw in kw_groups["secondary"]:
            if _matches_keyword(kw, text_lower, text_upper):
                score += 0.5

        if score > 0:
            scores[category] = score

    if not scores:
        return ("other", 0.0)

    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    if best_score >= 4.0:
        confidence = min(1.0, best_score / 6.0)
        return (best_cat, round(confidence, 2))
    elif best_score >= 1.5:
        confidence = min(0.65, best_score / 6.0)
        return (best_cat, round(confidence, 2))
    else:
        return ("other", 0.2)

