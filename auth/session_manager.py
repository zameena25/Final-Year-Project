#auth / session_manager.py

import secrets
from datetime import datetime, timedelta
from pathlib import Path
from .auth_db import get_connection


class SessionManager:

    TOKEN_BYTES   = 32
    REMEMBER_DAYS = 30
    NORMAL_HOURS  = 8

    def create_session(self, user_id: int, remember: bool = False) -> str:
        token = secrets.token_hex(self.TOKEN_BYTES)
        duration = (
            timedelta(days=self.REMEMBER_DAYS) if remember
            else timedelta(hours=self.NORMAL_HOURS)
        )
        expires = (datetime.now() + duration).isoformat()

        conn = get_connection()
        with conn:
            conn.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires)
            )
        conn.close()
        return token

    def validate_session(self, token: str):
        conn = get_connection()
        row = conn.execute(
            """SELECT s.user_id, u.username
               FROM sessions s JOIN users u ON s.user_id = u.id
               WHERE s.token = ? AND s.expires_at > datetime('now')""",
            (token,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def revoke_session(self, token: str):
        conn = get_connection()
        with conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.close()

    def save_token_to_disk(self, token: str):
        token_file = Path(__file__).parent.parent / ".session_token"
        token_file.write_text(token)

    def load_token_from_disk(self):
        token_file = Path(__file__).parent.parent / ".session_token"
        if token_file.exists():
            return token_file.read_text().strip()
        return None

    def clear_token_from_disk(self):
        token_file = Path(__file__).parent.parent / ".session_token"
        if token_file.exists():
            token_file.unlink()