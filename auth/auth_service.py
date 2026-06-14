#auth/auth_service.py
import bcrypt 
import uuid
from .auth_db import get_connection

class AuthService:
    def register(self, username: str, password: str) -> dict:
        """
        Returns: 
        {"success": True, "user_id": int}
        {"success": False, "error": str}
        """
        username = username.strip()
        if len (username) < 3:
            return{ "success" : False, "error": "Username must be at least 3 characters."}
        if len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters."}
        
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        conn = get_connection()
        try: 
            with conn: 
                cursor = conn.execute(
                    "INSERT INTO user (username, password_hash) VALUES(?,?)",
                    (username, hashed)
                )
                return {"success": True, "user_id": cursor.lastrowid}
        except Exception:
            return {"success": False, "error": "Username already exists."}
        finally:
            conn.close()
    
    #Login

    def login(self, username: str, password: str) -> dict:
        """
        Returns:
        {"success": True,  "user": Row, "requires_2fa": bool}
        {"success": False, "error": str}
        """
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username.strip(),)
            ).fetchone()
        finally:
            conn.close()
        
        if not row:
            return {"success": False, "error": "Invalid username or password."}
        
        if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return {"success":False, "error": "Invalid username or password."}
        
        return {
            "success": True,
            "user": dict(row),
            "requires_2fa": bool(row["totp_enabled"])
        }
    
    #guest access
    MAX_GUEST_USERS = 3
    def guest_access(self, machine_id: str) -> dict:
        """
        machine_id: any stable string identifying this machine (e.g. hostname).
        Returns:
        {"success": True, "users_left": int}
        {"success": False, "error": str}
        """
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT *FROM guest_usage WHERE identifier = ?", (machine_id,)
            ).fetchone()

            if row is None:
                with conn:
                    conn.execute(
                        "INSERT INTO guest_usage (identifier, uses) VALUES (?, 1)",
                        (machine_id,)
                    )
                uses = 1
            else:
                uses = row["uses"] + 1
                if uses > self.MAX_GUEST_USES:
                    return{
                        "success": False,
                        "error": f"Guest access limit reached ({self.MAX_GUEST_USES} uses). Please create an account."
                    }
                with conn:
                    conn.execute(
                        "UPDATE guest_usage SET uses = ?, last_used = datetime('now') WHERE identifier = ?",
                        (uses, machine_id)
                    )
            return{
                "success": True,
                "uses_left": self.MAX_GUEST_USES - uses
            }
        finally:
            conn.close()
