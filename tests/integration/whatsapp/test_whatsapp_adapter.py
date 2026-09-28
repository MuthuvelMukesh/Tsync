"""
Integration tests for WhatsApp notification provider with mocked HTTP layer.
"""

from unittest.mock import patch
import httpx
import pytest

from app.notifications.whatsapp import WhatsAppNotificationProvider


@pytest.mark.asyncio
async def test_whatsapp_notification_send_success():
    provider = WhatsAppNotificationProvider(
        access_token="fake_token",
        phone_number_id="10001",
    )

    fake_response = httpx.Response(
        status_code=200,
        json={"messages": [{"id": "wamid.HBgL..."}]},
        request=httpx.Request("POST", "https://graph.facebook.com"),
    )

    with patch.object(httpx.AsyncClient, "post", return_value=fake_response):
        result = await provider.send(
            recipient="+1234567890", message="Test WhatsApp message"
        )
        assert result.success
        assert result.external_message_id == "wamid.HBgL..."


@pytest.mark.asyncio
async def test_whatsapp_notification_missing_credentials():
    provider = WhatsAppNotificationProvider(access_token="", phone_number_id="")
    result = await provider.send(recipient="123", message="Hi")
    assert not result.success
    assert "not configured" in result.error
