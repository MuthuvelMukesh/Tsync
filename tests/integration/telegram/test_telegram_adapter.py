"""
Integration tests for Telegram notification provider and bot commands with mocked HTTP layer.
"""

from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.bots.telegram.commands import (
    execute_incidents_command,
    execute_search_command,
    execute_status_command,
)
from app.domain.incidents import Incident
from app.notifications.telegram import TelegramNotificationProvider


@pytest.mark.asyncio
async def test_telegram_notification_send_success():
    provider = TelegramNotificationProvider(bot_token="fake_bot_token")

    fake_response = httpx.Response(
        status_code=200,
        json={"ok": True, "result": {"message_id": 12345}},
        request=httpx.Request("POST", "https://api.telegram.org"),
    )

    with patch.object(httpx.AsyncClient, "post", return_value=fake_response):
        result = await provider.send(recipient="12345678", message="Test alert message")
        assert result.success
        assert result.external_message_id == "12345"


@pytest.mark.asyncio
async def test_telegram_bot_commands_execution():
    class MockIncService:
        async def get_hourly_updates(self, limit=15):
            return [Incident(1, "Semiconductor subsidies", "tech", importance_score=8.0)]

    class MockSearchService:
        async def search_incidents(self, query, limit=10):
            return [Incident(1, "Semiconductor subsidies", "tech", importance_score=8.0)]

    class MockStatusService:
        async def get_system_status(self):
            return {
                "status": "healthy",
                "active_sources_count": 2,
                "sources": ["source1", "source2"],
                "active_incidents_count": 1,
                "breaking_incidents_count": 0,
                "monitored_categories": ["tech"],
            }

    inc_msg = await execute_incidents_command(MockIncService())
    assert "Semiconductor subsidies" in inc_msg

    search_msg = await execute_search_command("semi", MockSearchService())
    assert "Semiconductor subsidies" in search_msg

    status_msg = await execute_status_command(MockStatusService())
    assert "HEALTHY" in status_msg
