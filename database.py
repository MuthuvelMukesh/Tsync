"""
database.py — SQLite storage layer for the Intelligence Engine.

Uses aiosqlite for async operations. Stores raw messages,
processed intelligence items, and daily reports.
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Optional


DB_PATH = "intelligence.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            text TEXT NOT NULL,
            category TEXT DEFAULT 'uncategorized',
            summary TEXT,
            why_it_matters TEXT,
            headline TEXT,
            importance_score REAL DEFAULT 0.0,
            date TEXT NOT NULL,
            source_channel TEXT NOT NULL,
            is_selected INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(telegram_id, source_channel)
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL UNIQUE,
            total_messages INTEGER DEFAULT 0,
            selected_count INTEGER DEFAULT 0,
            intensity TEXT DEFAULT 'LOW',
            categories_json TEXT,
            trends_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
        CREATE INDEX IF NOT EXISTS idx_messages_score ON messages(importance_score);
        CREATE INDEX IF NOT EXISTS idx_messages_selected ON messages(is_selected);
        CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(source_channel);
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


def insert_message(
    telegram_id: int,
    text: str,
    source_channel: str,
    msg_date: str
) -> Optional[int]:
    """Insert a raw message. Returns row ID or None if duplicate."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR IGNORE INTO messages
               (telegram_id, text, source_channel, date)
               VALUES (?, ?, ?, ?)""",
            (telegram_id, text, source_channel, msg_date)
        )
        conn.commit()
        return cursor.lastrowid if cursor.rowcount > 0 else None
    except sqlite3.Error as e:
        print(f"[DB] Insert error: {e}")
        return None
    finally:
        conn.close()


def bulk_insert_messages(messages: list[dict]) -> int:
    """Bulk insert messages. Returns count of new inserts."""
    conn = get_connection()
    inserted = 0
    try:
        cursor = conn.cursor()
        for msg in messages:
            cursor.execute(
                """INSERT OR IGNORE INTO messages
                   (telegram_id, text, source_channel, date)
                   VALUES (?, ?, ?, ?)""",
                (msg["telegram_id"], msg["text"],
                 msg["source_channel"], msg["date"])
            )
            if cursor.rowcount > 0:
                inserted += 1
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Bulk insert error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return inserted


def update_message_processing(
    msg_id: int,
    category: str,
    importance_score: float,
    headline: Optional[str] = None,
    summary: Optional[str] = None,
    why_it_matters: Optional[str] = None,
    is_selected: bool = False
) -> None:
    """Update a message with processing results."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE messages SET
               category = ?, importance_score = ?, headline = ?,
               summary = ?, why_it_matters = ?, is_selected = ?
               WHERE id = ?""",
            (category, importance_score, headline, summary,
             why_it_matters, int(is_selected), msg_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Update error: {e}")
    finally:
        conn.close()


def get_unprocessed_messages(target_date: Optional[str] = None) -> list[dict]:
    """Get messages that haven't been categorized yet."""
    conn = get_connection()
    if target_date is None:
        target_date = date.today().isoformat()
    try:
        rows = conn.execute(
            """SELECT id, telegram_id, text, source_channel, date
               FROM messages
               WHERE date = ? AND category = 'uncategorized'
               ORDER BY telegram_id DESC""",
            (target_date,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_messages_by_date(target_date: Optional[str] = None) -> list[dict]:
    """Get all messages for a given date."""
    conn = get_connection()
    if target_date is None:
        target_date = date.today().isoformat()
    try:
        rows = conn.execute(
            """SELECT * FROM messages WHERE date = ?
               ORDER BY importance_score DESC""",
            (target_date,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_selected_messages(target_date: Optional[str] = None) -> list[dict]:
    """Get only selected (high-value) messages for a date."""
    conn = get_connection()
    if target_date is None:
        target_date = date.today().isoformat()
    try:
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE date = ? AND is_selected = 1
               ORDER BY importance_score DESC""",
            (target_date,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_report_metadata(
    report_date: str,
    total_messages: int,
    selected_count: int,
    intensity: str,
    categories: dict,
    trends: list
) -> None:
    """Save report metadata for tracking."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO reports
               (report_date, total_messages, selected_count,
                intensity, categories_json, trends_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (report_date, total_messages, selected_count,
             intensity, json.dumps(categories), json.dumps(trends))
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Report save error: {e}")
    finally:
        conn.close()


def get_message_count_by_date(target_date: str) -> int:
    """Get total message count for a date."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE date = ?",
            (target_date,)
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()
