"""
Configuration management using Pydantic Settings.
Centralizes all environment variables and operational thresholds.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./tsync.db",
        description="Async database connection string (SQLite or PostgreSQL)",
    )

    # Telegram User Client (Ingestion)
    telegram_api_id: int = Field(default=0, description="Telegram API ID")
    telegram_api_hash: str = Field(default="", description="Telegram API Hash")
    telegram_session_name: str = Field(default="tsync_session", description="Telethon session file name")

    # Telegram Bot Adapter
    telegram_bot_token: str = Field(default="", description="Telegram Bot Token")
    telegram_alert_chat_id: str = Field(default="", description="Telegram chat ID for automated alerts")
    telegram_allowed_users: List[int] = Field(default_factory=list, description="Whitelisted user IDs for bot")

    # OpenRouter AI
    openrouter_api_key: str = Field(default="", description="OpenRouter API Key")
    openrouter_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="OpenRouter model identifier",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter base API URL",
    )

    # WhatsApp Cloud API
    whatsapp_access_token: str = Field(default="", description="Meta WhatsApp Cloud API Access Token")
    whatsapp_phone_number_id: str = Field(default="", description="Meta WhatsApp Phone Number ID")
    whatsapp_recipient_phone: str = Field(default="", description="Default recipient WhatsApp phone number")

    # Pipeline & Incident Engine Defaults
    timezone: str = Field(default="Asia/Kolkata", description="Application default timezone")
    breaking_score: float = Field(default=8.5, description="Threshold for immediate breaking alerts")
    importance_threshold: float = Field(default=7.0, description="Base score for high-signal item selection")
    min_items: int = Field(default=5, description="Minimum items in digest")
    max_items: int = Field(default=15, description="Maximum items in digest")
    min_message_length: int = Field(default=30, description="Minimum characters for filtering noise")
    channels: List[str] = Field(
        default=["duaborobot", "techaborobot"],
        description="Default Telegram channel usernames to monitor",
    )

    environment: str = Field(default="development", description="Runtime environment")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retrieve or initialize application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
