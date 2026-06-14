#auth /  auth_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "novasphere_auth.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables on first run. Call once at app startup."""
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                totp_secret   TEXT,
                totp_enabled  INTEGER DEFAULT 0,
                created_at    TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                token      TEXT    UNIQUE NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                expires_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS guest_usage (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT    UNIQUE NOT NULL,
                uses       INTEGER DEFAULT 0,
                last_used  TEXT    DEFAULT (datetime('now'))
            );
        """)
    conn.close()