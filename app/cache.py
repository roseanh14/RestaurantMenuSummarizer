import sqlite3
import json
from datetime import datetime, timezone

from .config import DB_PATH


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_cache (
            url TEXT NOT NULL,
            date TEXT NOT NULL,
            menu_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (url, date)
        )
        """
    )
    conn.commit()
    conn.close()


def delete_old_cache(today_iso: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM menu_cache WHERE date < ?", (today_iso,))
        conn.commit()
    except sqlite3.OperationalError as e:
        conn.close()
        if "no such table" in str(e):
            init_db()
            return
        raise
    else:
        conn.close()


def get_cached_menu(url: str, date_iso: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        (url, date_iso),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


def save_cached_menu(url: str, date_iso: str, menu: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO menu_cache (url, date, menu_json, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            url,
            date_iso,
            json.dumps(menu, ensure_ascii=False),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
