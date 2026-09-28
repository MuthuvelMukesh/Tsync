"""
Authentication and authorization check for Telegram bot commands.
"""

from typing import List


def is_user_authorized(user_id: int, allowed_user_ids: List[int]) -> bool:
    """Check if telegram user ID is whitelisted. If allowed list is empty, permit all."""
    if not allowed_user_ids:
        return True
    return user_id in allowed_user_ids
