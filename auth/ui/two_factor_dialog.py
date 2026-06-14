#auth/ui/two_factor_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from auth.totp_service import TOTPService


class TwoFactorDialog(QDialog):
    """Pops up after password verification when 2FA is enabled."""

    def __init__(self, user_id: int, username: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.totp_svc = TOTPService()
        self.verified = False

        self.setWindowTitle("Two-Factor Authentication")
        self.setFixedSize(380, 220)
        self.setModal(True)
        self._build_ui(username)

    def _build_ui(self, username: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Verification Required")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(f"Enter the 6-digit code for\n{username}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(subtitle)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("000000")
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setFixedHeight(44)
        self.code_input.setFont(QFont("Segoe UI", 18))
        self.code_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #444;
                border-radius: 8px;
                background: #1a1a2e;
                color: white;
                letter-spacing: 8px;
            }
            QLineEdit:focus { border-color: #7c3aed; }
        """)
        # Auto-submit when 6 digits are entered
        self.code_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.code_input)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.verify_btn = QPushButton("Verify")
        self.verify_btn.setFixedHeight(36)
        self.verify_btn.setEnabled(False)
        self.verify_btn.setDefault(True)
        self.verify_btn.clicked.connect(self._verify)
        self.verify_btn.setStyleSheet("background: #7c3aed; color: white; border-radius: 6px;")
        btn_row.addWidget(self.verify_btn)
        layout.addLayout(btn_row)

    def _on_text_changed(self, text: str):
        # Only allow digits
        digits = ''.join(c for c in text if c.isdigit())
        if digits != text:
            self.code_input.setText(digits)
            return
        self.verify_btn.setEnabled(len(digits) == 6)
        if len(digits) == 6:
            self._verify()

    def _verify(self):
        code = self.code_input.text().strip()
        if self.totp_svc.verify_code(self.user_id, code):
            self.verified = True
            self.accept()
        else:
            self.code_input.clear()
            self.code_input.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #e74c3c;
                    border-radius: 8px;
                    background: #1a1a2e;
                    color: white;
                    letter-spacing: 8px;
                }
            """)
            QMessageBox.warning(self, "Invalid Code", "The code is incorrect. Please try again.")
            self.code_input.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #444;
                    border-radius: 8px;
                    background: #1a1a2e;
                    color: white;
                    letter-spacing: 8px;
                }
                QLineEdit:focus { border-color: #7c3aed; }
            """)
