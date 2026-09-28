"""
Backfill and demo workflow for populating and reprocessing historical or synthetic data.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.domain.messages import Message
from app.processing.categorization import categorize_by_rules
from app.processing.normalization import clean_text
from app.processing.scoring import score_message
from app.reports.daily import DailyReportGenerator
from app.services.briefing_service import BriefingService
from app.services.incident_service import IncidentService
from app.storage.repositories.messages import MessageRepository

DEFAULT_DEMO_DATA = [
    {
        "external_id": "demo-001",
        "source_channel": "tech_news",
        "text": "BREAKING: OpenAI announces GPT-5 with unprecedented reasoning capabilities. The new model achieves 95% on graduate-level science benchmarks and introduces native multimodal understanding. Enterprise software and scientific research sectors are poised for major disruption.",
        "category": "technology",
    },
    {
        "external_id": "demo-002",
        "source_channel": "finance_daily",
        "text": "Federal Reserve signals potential rate cut in September as inflation data cools. CPI dropped to 2.4% year-over-year. S&P 500 gained 1.8% as bond yields fell sharply.",
        "category": "finance",
    },
    {
        "external_id": "demo-003",
        "source_channel": "regulation_watch",
        "text": "EU passes comprehensive AI regulation framework requiring transparency disclosures for all deployed AI systems. Penalties up to 6% of global revenue for non-compliance.",
        "category": "regulation",
    },
    {
        "external_id": "demo-004",
        "source_channel": "tech_news",
        "text": "NVIDIA reports record quarterly revenue of $35.1 billion, driven by surging demand for AI training chips. Data center revenue up 427% year-over-year. CEO Jensen Huang announces Blackwell Ultra architecture.",
        "category": "technology",
    },
    {
        "external_id": "demo-005",
        "source_channel": "cyber_alert",
        "text": "Major cybersecurity breach at healthcare giant exposes 12 million patient records. Hackers exploited zero-day vulnerability in cloud infrastructure. FBI investigation launched.",
        "category": "technology",
    },
    {
        "external_id": "demo-006",
        "source_channel": "science_today",
        "text": "NASA confirms discovery of organic molecules on Mars surface by Perseverance rover in Jezero Crater sediments. Biological activity cannot be ruled out.",
        "category": "science",
    },
    {
        "external_id": "demo-007",
        "source_channel": "tech_news",
        "text": "OpenAI confirms rollout schedule for GPT-5 early access program, partnering with Fortune 50 enterprises and scientific labs starting next Monday.",
        "category": "technology",
    },
]


async def run_backfill_workflow(
    message_repo: MessageRepository,
    incident_service: IncidentService,
    briefing_service: BriefingService,
    sample_records: Optional[List[dict]] = None,
    output_html_path: str = "report.html",
    output_txt_path: str = "report.txt",
) -> dict:
    """Populate system with sample/historical data and process into incident domain."""
    records = sample_records or DEFAULT_DEMO_DATA
    now = datetime.now(timezone.utc)

    print(f"\n[WORKFLOW:BACKFILL] Seeding {len(records)} sample messages...")

    domain_messages: List[Message] = []
    for rec in records:
        text = rec["text"]
        cat = rec.get("category") or categorize_by_rules(text)[0]
        score = score_message(text=text, category=cat, source_channel=rec["source_channel"])

        msg = Message(
            id=None,
            external_id=rec["external_id"],
            source_channel=rec["source_channel"],
            text=text,
            cleaned_text=clean_text(text),
            published_at=now,
            category=cat,
            importance_score=score,
            is_selected=score >= 7.0,
        )
        domain_messages.append(msg)

    saved_messages = await message_repo.bulk_create(domain_messages)
    print(f"[WORKFLOW:BACKFILL] Stored {len(saved_messages)} messages in database.")

    # Process each through IncidentService
    incidents_updated = 0
    for msg in saved_messages:
        res = await incident_service.process_message(msg)
        if res:
            incidents_updated += 1

    # Generate Digest
    active = await incident_service.get_hourly_updates(limit=50)
    digest = briefing_service.generate_digest(active, period="daily")

    DailyReportGenerator.generate_html(digest, output_path=output_html_path)
    DailyReportGenerator.generate_text(digest, output_path=output_txt_path)

    print(f"[WORKFLOW:BACKFILL] Completed backfill. {len(active)} active incidents generated.")
    return {
        "messages_seeded": len(saved_messages),
        "incidents_created": len(active),
        "intensity": digest.intensity,
        "html_report": output_html_path,
        "txt_report": output_txt_path,
    }
