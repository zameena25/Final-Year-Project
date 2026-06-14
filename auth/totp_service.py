#auth/totp_service.py

import pyotp
import qrcode
import io
from .auth_db import get_connection

class TOTPService:
    APP_NAME = "NOVASPHERE"

    def setup_totp(self,user_id: int, username: str) -> dict:
        """
        Generate a new TOTP secret for the user and return:
          - the secret (store this in the DB)
          - a QR code as bytes (show this in a QLabel with a pixmap)
          - the manual-entry URI string
        """
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=self.APP_NAME)

        qr = qrcode.make(uri)
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        qr_bytes = buf.getvalue()

        # Save the secret to the DB
        conn = get_connection()
        with conn:
            conn.execute(
                "UPDATE users SET totp_secret = ? WHERE id = ?",
                (secret, user_id)
            )
        conn.close()

        return {"secret": secret, "qr_bytes": qr_bytes, "uri": uri}
    
    def verify_code(self, user_id: int, code: str) -> bool:
        """
        Verify a 6-digit TOTP code. Returns True if valid.
        """
        conn = get_connection()
        row = conn.execute(
            "SELECT totp_secret FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        conn.close()
        
        if not row or not row ["totp_secret"]:
            return False
        
        totp =  pyotp.TOTP(row["totp_secret"])
        return totp.verify(code, valid_window=1)
    
    def enable_totp(self, user_id: int):
        """Call this after the user successfully verifies their first code."""
        conn = get_connection()
        with conn:
            conn.execute(
                "UPDATE users SET totp_enabled = 1 WHERE id = ?", (user_id,)
            )
        conn.close()
        
