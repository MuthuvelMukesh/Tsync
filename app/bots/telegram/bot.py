"""
Telegram bot application lifecycle manager and runner.
"""

from typing import List, Optional
from telegram.ext import Application, ApplicationBuilder, CommandHandler

from app.bots.telegram.handlers import TelegramBotHandlers
from app.services.briefing_service import BriefingService
from app.services.incident_service import IncidentService
from app.services.search_service import SearchService
from app.services.status_service import StatusService


class TelegramBot:
    """Manages Telegram bot application and update polling."""

    def __init__(
        self,
        token: str,
        incident_service: IncidentService,
        search_service: SearchService,
        briefing_service: BriefingService,
        status_service: StatusService,
        allowed_user_ids: Optional[List[int]] = None,
    ):
        self.token = token
        self.handlers = TelegramBotHandlers(
            incident_service=incident_service,
            search_service=search_service,
            briefing_service=briefing_service,
            status_service=status_service,
            allowed_user_ids=allowed_user_ids or [],
        )
        self.app: Optional[Application] = None

    def build_application(self) -> Application:
        """Construct the telegram application and bind handlers."""
        app = ApplicationBuilder().token(self.token).build()

        app.add_handler(CommandHandler("start", self.handlers.start))
        app.add_handler(CommandHandler("help", self.handlers.help_cmd))
        app.add_handler(CommandHandler("incidents", self.handlers.incidents))
        app.add_handler(CommandHandler("details", self.handlers.details))
        app.add_handler(CommandHandler("search", self.handlers.search))
        app.add_handler(CommandHandler("briefing", self.handlers.briefing))
        app.add_handler(CommandHandler("status", self.handlers.status))

        self.app = app
        return app

    def run_polling(self) -> None:
        """Start the bot in long-polling mode (blocking)."""
        if not self.token:
            print("[BOT] Error: Telegram bot token not configured.")
            return

        app = self.build_application()
        print("[BOT] Starting Telegram Bot polling...")
        app.run_polling()
