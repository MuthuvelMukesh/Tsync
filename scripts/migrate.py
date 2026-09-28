"""
Database migration and schema initialization script.
Usage:
  python scripts/migrate.py
"""

import asyncio
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.storage.database import init_db, close_db


async def main():
    settings = get_settings()
    print(f"⚡ Initializing Tsync Database at: {settings.database_url}")
    await init_db(settings.database_url)
    await close_db()
    print("✅ Database tables successfully created/verified.")


if __name__ == "__main__":
    asyncio.run(main())
