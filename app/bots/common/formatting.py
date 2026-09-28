"""
Common bot formatting helpers.
"""

import re


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram legacy Markdown."""
    # Escape Markdown special characters except basic formatting if needed
    escape_chars = r"_*`["
    return re.sub(r"([%s])" % re.escape(escape_chars), r"\\\1", text)


def format_error(message: str) -> str:
    """Format standardized error response."""
    return f"❌ *Error:* {message}"


def format_success(message: str) -> str:
    """Format standardized success response."""
    return f"✅ {message}"
