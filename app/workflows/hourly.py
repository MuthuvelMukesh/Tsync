"""
Hourly workflow orchestrating ingestion, processing, incident updates, and digest distribution.
Coordinates services without containing business logic.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.ingestion.service import IngestionService
from app.notifications.dispatcher import NotificationDispatcher
from app.processing.categorization import categorize_by_rules
from app.processing.scoring import score_message
from app.reports.daily import DailyReportGenerator
from app.reports.formatters import format_telegram_markdown
from app.services.briefing_service import BriefingService
from app.services.incident_service import IncidentService
from app.storage.repositories.messages import MessageRepository


async def run_hourly_workflow(
    ingestion_service: IngestionService,
    message_repo: MessageRepository,
    incident_service: IncidentService,
    briefing_service: BriefingService,
    notification_dispatcher: Optional[NotificationDispatcher] = None,
    lookback_hours: int = 2,
    output_html_path: str = "report.html",
    output_txt_path: str = "report.txt",
) -> dict:
    """
    Executes the standard hourly intelligence pipeline cycle:
    Ingest → Process → Incidents → Digest → Dispatch
    """
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=lookback_hours)

    print(f"\n[WORKFLOW:HOURLY] Starting cycle from {start_time.strftime('%H:%M')} to {now.strftime('%H:%M')} UTC")

    # 1. Ingestion
    ingest_stats = await ingestion_service.ingest_all(start_time=start_time, end_time=now)
    total_new = sum(s.new_stored for s in ingest_stats)
    print(f"[WORKFLOW:HOURLY] Ingestion complete: {total_new} new messages stored")

    # 2. Retrieve and process uncategorized messages
    unprocessed = await message_repo.get_unprocessed(limit=200)
    for msg in unprocessed:
        # Rule-based categorization
        category, confidence = categorize_by_rules(msg.cleaned_text)
        msg.category = category
        # Heuristic scoring
        msg.importance_score = score_message(
            text=msg.cleaned_text,
            category=category,
            source_channel=msg.source_channel,
        )
        msg.is_selected = msg.importance_score >= 7.0
        await message_repo.update(msg)

        # 3. Update Incident Domain Model
        await incident_service.process_message(msg)

    # 4. Compile Hourly Digest
    active_incidents = await incident_service.get_hourly_updates(limit=25)
    digest = briefing_service.generate_digest(active_incidents, period="hourly")
    print(f"[WORKFLOW:HOURLY] Active incidents: {len(active_incidents)} | Intensity: {digest.intensity}")

    # 5. Generate Reports
    DailyReportGenerator.generate_html(digest, output_path=output_html_path)
    DailyReportGenerator.generate_text(digest, output_path=output_txt_path)

    # 6. Notification Delivery
    dispatch_results = []
    if notification_dispatcher:
        digest_msg = format_telegram_markdown(digest)
        dispatch_results = await notification_dispatcher.broadcast(
            digest_msg, event_type="hourly_digest"
        )

    print("[WORKFLOW:HOURLY] Cycle finished successfully.")
    return {
        "status": "success",
        "new_messages_ingested": total_new,
        "processed_count": len(unprocessed),
        "active_incidents": len(active_incidents),
        "intensity": digest.intensity,
        "html_report": output_html_path,
        "txt_report": output_txt_path,
        "dispatches": len(dispatch_results),
    }
