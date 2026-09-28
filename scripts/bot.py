"""
Telegram Bot runner script.
Usage:
  python scripts/bot.py
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
from app.storage.database import get_session_factory, init_db
from app.storage.repositories.messages import SQLAlchemyMessageRepository
from app.storage.repositories.incidents import SQLAlchemyIncidentRepository
from app.storage.repositories.sources import SQLAlchemySourceRepository
from app.storage.repositories.entities import SQLAlchemyEntityRepository
from app.services.incident_service import IncidentService
from app.services.search_service import SearchService
from app.services.briefing_service import BriefingService
from app.services.status_service import StatusService
from app.bots.telegram.bot import TelegramBot


async def init_services():
    settings = get_settings()
    await init_db(settings.database_url)
    session_factory = get_session_factory()

    incident_repo = SQLAlchemyIncidentRepository(session_factory)
    message_repo = SQLAlchemyMessageRepository(session_factory)
    source_repo = SQLAlchemySourceRepository(session_factory)
    entity_repo = SQLAlchemyEntityRepository(session_factory)

    incident_service = IncidentService(
        incident_repo=incident_repo,
        message_repo=message_repo,
    )
    search_service = SearchService(
        incident_repo=incident_repo,
        entity_repo=entity_repo,
    )
    briefing_service = BriefingService()
    status_service = StatusService(
        incident_repo=incident_repo,
        source_repo=source_repo,
    )

    return incident_service, search_service, briefing_service, status_service, settings


def main():
    incident_service, search_service, briefing_service, status_service, settings = asyncio.run(
        init_services()
    )

    if not settings.telegram_bot_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not set in environment or .env")
        print("Please configure your bot token before running scripts/bot.py")
        sys.exit(1)

    bot = TelegramBot(
        token=settings.telegram_bot_token,
        incident_service=incident_service,
        search_service=search_service,
        briefing_service=briefing_service,
        status_service=status_service,
        allowed_user_ids=settings.telegram_allowed_users,
    )

    bot.run_polling()


if __name__ == "__main__":
    main()
