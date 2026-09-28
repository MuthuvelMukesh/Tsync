"""
Telegram update handlers for commands and messages.
"""

import re
from typing import List
from telegram import Update
from telegram.ext import ContextTypes

from app.bots.telegram.auth import is_user_authorized
from app.bots.telegram.commands import (
    execute_briefing_command,
    execute_details_command,
    execute_incidents_command,
    execute_search_command,
    execute_status_command,
    get_help_message,
    get_start_message,
)
from app.services.briefing_service import BriefingService
from app.services.incident_service import IncidentService
from app.services.search_service import SearchService
from app.services.status_service import StatusService


class TelegramBotHandlers:
    """Binds Telegram updates to service controllers."""

    def __init__(
        self,
        incident_service: IncidentService,
        search_service: SearchService,
        briefing_service: BriefingService,
        status_service: StatusService,
        allowed_user_ids: List[int],
    ):
        self.incident_service = incident_service
        self.search_service = search_service
        self.briefing_service = briefing_service
        self.status_service = status_service
        self.allowed_user_ids = allowed_user_ids

    def _check_auth(self, update: Update) -> bool:
        user = update.effective_user
        if not user:
            return False
        return is_user_authorized(user.id, self.allowed_user_ids)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return
        await update.message.reply_text(get_start_message(), parse_mode="Markdown")

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return
        await update.message.reply_text(get_help_message(), parse_mode="Markdown")

    async def incidents(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return
        msg = await execute_incidents_command(self.incident_service)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def details(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return

        text = update.message.text or ""
        # Support /details 123 or /details_123
        match = re.search(r"/details_?(\d+)", text)
        if not match and context.args:
            match = re.search(r"(\d+)", context.args[0])

        if not match:
            await update.message.reply_text(
                "⚠️ Please specify an incident ID: `/details <id>`", parse_mode="Markdown"
            )
            return

        incident_id = int(match.group(1))
        msg = await execute_details_command(incident_id, self.incident_service)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return

        query = " ".join(context.args) if context.args else ""
        msg = await execute_search_command(query, self.search_service)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def briefing(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return
        msg = await execute_briefing_command(self.incident_service, self.briefing_service)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._check_auth(update) or not update.message:
            return
        msg = await execute_status_command(self.status_service)
        await update.message.reply_text(msg, parse_mode="Markdown")
