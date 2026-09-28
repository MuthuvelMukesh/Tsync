"""
Hourly intelligence runner CLI script.
Usage:
  python scripts/hourly.py          # Standard hourly run
  python scripts/hourly.py --demo   # Seed sample data and generate report
"""

import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.storage.database import get_session_factory, init_db, close_db
from app.storage.repositories.messages import SQLAlchemyMessageRepository
from app.storage.repositories.incidents import SQLAlchemyIncidentRepository
from app.storage.repositories.sources import SQLAlchemySourceRepository
from app.storage.repositories.notifications import SQLAlchemyNotificationAuditRepository
from app.ingestion.telegram import TelegramMessageSource
from app.ingestion.service import IngestionService
from app.notifications.telegram import TelegramNotificationProvider
from app.notifications.whatsapp import WhatsAppNotificationProvider
from app.notifications.dispatcher import NotificationDispatcher
from app.intelligence.summarizer import IntelligenceSummarizer
from app.ai.openrouter import OpenRouterAIProvider
from app.services.incident_service import IncidentService
from app.services.briefing_service import BriefingService
from app.workflows.hourly import run_hourly_workflow
from app.workflows.backfill import run_backfill_workflow


async def main():
    settings = get_settings()
    await init_db(settings.database_url)
    session_factory = get_session_factory()

    # Repositories
    message_repo = SQLAlchemyMessageRepository(session_factory)
    incident_repo = SQLAlchemyIncidentRepository(session_factory)
    source_repo = SQLAlchemySourceRepository(session_factory)
    audit_repo = SQLAlchemyNotificationAuditRepository(session_factory)

    # Ingestion sources
    active_channels = await source_repo.list_active()
    if not active_channels:
        active_channels = settings.channels

    telegram_source = TelegramMessageSource(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        channels=active_channels,
        session_name=settings.telegram_session_name,
    )
    ingestion_service = IngestionService(
        message_repo=message_repo,
        sources=[telegram_source],
    )

    # AI Provider & Summarizer
    ai_provider = None
    if settings.openrouter_api_key:
        ai_provider = OpenRouterAIProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
        )
    summarizer = IntelligenceSummarizer(ai_provider=ai_provider)

    # Incident & Briefing Services
    incident_service = IncidentService(
        incident_repo=incident_repo,
        message_repo=message_repo,
        summarizer=summarizer,
    )
    briefing_service = BriefingService()

    # Notification Dispatcher
    providers = []
    if settings.telegram_bot_token:
        providers.append(TelegramNotificationProvider(settings.telegram_bot_token))
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
        providers.append(
            WhatsAppNotificationProvider(
                access_token=settings.whatsapp_access_token,
                phone_number_id=settings.whatsapp_phone_number_id,
            )
        )

    dispatcher = NotificationDispatcher(
        providers=providers,
        audit_repo=audit_repo,
        default_telegram_chat_id=settings.telegram_alert_chat_id,
        default_whatsapp_phone=settings.whatsapp_recipient_phone,
    )

    is_demo = "--demo" in sys.argv
    if is_demo:
        print("⚡ Running in DEMO mode with realistic sample incidents...")
        res = await run_backfill_workflow(
            message_repo=message_repo,
            incident_service=incident_service,
            briefing_service=briefing_service,
        )
        print(f"✅ Demo run complete: {res['incidents_created']} incidents processed.")
        print(f"📊 Report generated at: {res['html_report']}")
    else:
        res = await run_hourly_workflow(
            ingestion_service=ingestion_service,
            message_repo=message_repo,
            incident_service=incident_service,
            briefing_service=briefing_service,
            notification_dispatcher=dispatcher,
        )
        print(f"✅ Hourly workflow complete. Active incidents: {res['active_incidents']}")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
