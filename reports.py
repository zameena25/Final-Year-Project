# reports_page.py  ── NovaSphere Security Reports Page
# Pixel-perfect match to screenshots. Plug into dashboard.py:
#   from reports_page import ReportsPage
#   (" Reports", ReportsPage()),
# frontend / reports.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QLineEdit, QDialog,
    QFormLayout, QComboBox, QTimeEdit, QSizePolicy, QGridLayout,
    QSpacerItem, QTextEdit
)
from PyQt6.QtCore import Qt, QTime, QRectF, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QFont, QPen, QLinearGradient, QFontMetrics
)

# ── Colour tokens ──────────────────────────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_SIDEBAR = "#0d1120"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
BG_ROW_H   = "#0f1828"
CYAN       = "#00bcd4"
CYAN_DIM   = "#007a8a"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"
RED        = "#ef5350"
ORANGE     = "#ffa726"
GREEN_A    = "#66bb6a"
BLUE_A     = "#42a5f5"
PURPLE_A   = "#ab47bc"
GREEN_ACT  = "#00c853"

PAGE_STYLE = f"""
    QWidget {{ font-family: 'Segoe UI', sans-serif; background: transparent; color: {TEXT_WHITE}; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: {BG_MAIN}; width: 5px; border-radius: 2px; }}
    QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 2px; min-height: 30px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QLineEdit {{
        background: #111827; border: 1px;
        border-radius: 8px; color: {TEXT_WHITE}; font-size: 13px; padding: 6px 12px;
    }}
    QLineEdit:focus {{ border: 1px solid {CYAN}; }}
    QComboBox, QTimeEdit {{
        background: #111827; border: 1px solid {BORDER};
        border-radius: 6px; color: {TEXT_WHITE}; font-size: 13px; padding: 5px 10px;
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{ background: #111827; color: {TEXT_WHITE}; selection-background-color: {CYAN}; }}
"""

# ── Donut chart ────────────────────────────────────────────────────────────────
class DonutChart(QWidget):
    # Clockwise from 12 o clock: Red(large) then Orange then Blue then Green then Purple(tiny)
    SLICES = [
        (34, QColor(RED)),
        (28, QColor(ORANGE)),
        (20, QColor(BLUE_A)),
        (12, QColor(GREEN_A)),
        (6,  QColor(PURPLE_A)),
    ]
    GAP_DEG = 2.2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 10
        size = min(self.width(), self.height()) - m * 2
        x = (self.width()  - size) // 2
        y = (self.height() - size) // 2
        arc = QRectF(x, y, size, size)
        # Thinner ring = large hollow centre matching target UI
        ring = int(size * 0.20)
        total = sum(s[0] for s in self.SLICES)
        gap16 = int(self.GAP_DEG * 16)
        # Start at ~60deg (between 12 and 3 oclock) so Red lands top-right
        # as in the design mockup. Negative span = clockwise direction.
        angle = 60 * 16
        for pct, color in self.SLICES:
            full_span = int(pct / total * 360 * 16)
            draw_span = max(full_span - gap16, 1)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawPie(arc, angle, -draw_span)
            angle -= full_span
        # Hollow centre punch-out
        inner = size - ring * 2
        p.setBrush(QBrush(QColor(BG_CARD)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(x + ring, y + ring, inner, inner))
        p.end()


# ── Compliance bar ─────────────────────────────────────────────────────────────
class ComplianceBar(QWidget):
    def __init__(self, label, pct, parent=None):
        super().__init__(parent)
        self._label = label
        self._pct   = pct
        self.setFixedHeight(28)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        lw = 62

        p.setPen(QColor(TEXT_MUTED))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(0, 0, lw, h, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self._label)

        tx = lw + 12
        tw = w - tx - 44
        bar_h = 7
        by = h // 2 - bar_h // 2

        p.setBrush(QBrush(QColor(BORDER)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(tx, by, tw, bar_h), 3, 3)

        fw = int(tw * self._pct / 100)
        grad = QLinearGradient(tx, 0, tx + fw, 0)
        grad.setColorAt(0, QColor(CYAN_DIM))
        grad.setColorAt(1, QColor(CYAN))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(QRectF(tx, by, fw, bar_h), 3, 3)

        p.setPen(QColor(TEXT_WHITE))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(int(tx + tw + 8), 0, 36, h,
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   f"{self._pct}%")
        p.end()


# ── Separator ──────────────────────────────────────────────────────────────────
def sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {BORDER}; border: none;")
    return f


# ── Report Preview Dialog ──────────────────────────────────────────────────────
class ReportPreviewDialog(QDialog):
    CONTENT = {
        "Weekly Executive Summary": (
            "Executive",
            "May 15, 2025",
            "System (Auto)",
            """WEEKLY EXECUTIVE SECURITY SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Period: May 9 – May 15, 2025
Classification: CONFIDENTIAL

EXECUTIVE OVERVIEW
──────────────────
Security posture remains ELEVATED. 3 critical incidents were detected
and contained this week. No data exfiltration confirmed.

KEY METRICS
───────────
  Total Alerts Generated    :  1,247
  Critical Incidents        :      3
  Threats Neutralised       :     41
  Systems Quarantined       :      2
  Mean Time to Detect (MTTD):  4.2 min
  Mean Time to Respond (MTTR): 11.7 min

TOP THREATS THIS WEEK
─────────────────────
  1. Ransomware variant LockBit 3.1 detected on FINANCE-WS-04
     → Quarantined and remediated within 8 minutes.

  2. Phishing campaign targeting HR department (14 emails blocked).

  3. Lateral movement attempt from compromised service account
     → Account disabled, investigation ongoing.

COMPLIANCE STATUS
─────────────────
  HIPAA   ████████████████████░  91 %
  GDPR    ████████████████████   84 %
  PCI-DSS ███████████████░░░░░   73 %
  SOC2    ████████████████████   88 %

RECOMMENDATIONS
───────────────
  • Enforce MFA on all privileged accounts immediately.
  • Patch CVE-2025-1234 on remaining 6 unpatched endpoints.
  • Review service-account permission scopes.

Report generated automatically by NovaSphere v2.4
""",
        ),
        "Ransomware Incident Analysis": (
            "Incident",
            "May 14, 2025",
            "Admin",
            """RANSOMWARE INCIDENT ANALYSIS REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Incident ID : INC-2025-0514-001
Severity    : CRITICAL
Status      : RESOLVED

INCIDENT TIMELINE
─────────────────
  08:14  Initial file encryption activity detected on FINANCE-WS-04.
  08:15  Automated quarantine triggered — host isolated from network.
  08:17  Analyst notified via NovaSphere alert.
  08:22  Threat identified: LockBit 3.1 variant.
  08:23  EDR rollback initiated — 98 % of files recovered.
  08:31  Host returned to clean snapshot.
  08:45  Root-cause: phishing email opened 2025-05-13 22:47.

AFFECTED SYSTEMS
────────────────
  FINANCE-WS-04   (Primary victim)
  FINANCE-FS-01   (Attempted lateral move — blocked)

INDICATORS OF COMPROMISE (IOCs)
────────────────────────────────
  File hash  : 3b4c2d1e8f...a9c0 (SHA-256)
  C2 domain  : update-cdn-secure[.]xyz
  Reg key    : HKCU\\Software\\LockBit\\Config

REMEDIATION STEPS TAKEN
────────────────────────
  ✓ Host quarantined and reimaged.
  ✓ C2 domain blocked at perimeter firewall.
  ✓ IOCs pushed to all endpoints via EDR.
  ✓ Phishing email removed from all mailboxes.
  ✓ User awareness training scheduled.

Report authored by: Admin
""",
        ),
        "User Activity Audit - Finance": (
            "Compliance",
            "May 12, 2025",
            "J. Doe",
            """USER ACTIVITY AUDIT — FINANCE DEPARTMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Audit Period : April 1 – April 30, 2025
Auditor      : J. Doe
Scope        : 34 Finance department user accounts

SUMMARY
───────
  Accounts Reviewed       : 34
  Policy Violations Found :  6
  Anomalies Flagged       :  9
  Accounts Suspended      :  1

NOTABLE FINDINGS
────────────────
  1. jsmith@corp — Accessed payroll data outside business hours
     on 7 occasions. Under review.

  2. service-acct-fin — Privilege escalation attempt detected.
     Account privileges reduced.

  3. contractor-04 — Data download volume 340 % above baseline
     on April 22. HR notified.

ACCESS PATTERN ANALYSIS
───────────────────────
  Peak access hours   : 09:00 – 17:00  (expected)
  Off-hours access    : 12 events across 5 accounts
  Geo anomalies       :  2 (VPN from non-approved regions)
  Failed logins > 5   :  3 accounts

RECOMMENDATIONS
───────────────
  • Revoke contractor-04 access pending investigation.
  • Enforce time-based access controls for payroll systems.
  • Implement DLP policy for bulk data exports.

Report prepared by: J. Doe | Compliance Team
""",
        ),
        "Monthly Threat Landscape": (
            "Strategic",
            "May 01, 2025",
            "System (Auto)",
            """MONTHLY THREAT LANDSCAPE REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Period       : April 2025
Generated by : NovaSphere Automated Intelligence

THREAT ENVIRONMENT OVERVIEW
────────────────────────────
Global threat activity increased 14 % month-over-month.
Ransomware remains the dominant attack vector (34 % of incidents).
Supply-chain attacks targeting SaaS integrations rose by 22 %.

ATTACK VECTOR BREAKDOWN
────────────────────────
  Ransomware        34 %  ████████████████████
  Phishing          28 %  ████████████████░░░░
  Insider Threat    20 %  ████████████░░░░░░░░
  Malware           12 %  ███████░░░░░░░░░░░░░
  Other              6 %  ████░░░░░░░░░░░░░░░░

EMERGING THREATS
────────────────
  • AI-generated spear-phishing emails bypassing legacy filters.
  • Zero-day in widely used VPN appliance (CVE-2025-9981) — patch now.
  • Credential-stuffing campaigns leveraging leaked databases.

RECOMMENDATIONS FOR MAY 2025
──────────────────────────────
  1. Deploy AI-aware email filtering (priority: HIGH).
  2. Patch CVE-2025-9981 on all VPN gateways within 48 hours.
  3. Rotate credentials for shared service accounts.
  4. Conduct red-team exercise targeting supply-chain vectors.

NovaSphere Threat Intelligence | Automated Monthly Digest
""",
        ),
    }

    def __init__(self, report_name: str, parent=None):
        super().__init__(parent)
        data = self.CONTENT.get(report_name, (
            "Unknown", "–", "–",
            f"No preview content available for:\n{report_name}"
        ))
        rtype, date, author, content = data

        self.setWindowTitle(f"Report Preview — {report_name}")
        self.setModal(True)
        self.resize(740, 580)
        self.setStyleSheet(f"""
            QDialog  {{ background: {BG_CARD2}; border-radius: 14px; }}
            QWidget  {{ background: transparent; color: {TEXT_WHITE};
                        font-family: 'Segoe UI', sans-serif; }}
            QTextEdit {{
                background: #0b0f1a; color: {TEXT_WHITE};
                border: 1px solid {BORDER}; border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px; padding: 12px;
            }}
            QPushButton {{
                background: {CYAN}; color: #000; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 9px 24px;
            }}
            QPushButton:hover {{ background: #00eeff; }}
            QPushButton#close_btn {{
                background: {BG_CARD}; color: {TEXT_MUTED};
                border: 1px solid {BORDER};
            }}
            QPushButton#close_btn:hover {{ color: {TEXT_WHITE}; border-color: {TEXT_MUTED}; }}
        """)

        vl = QVBoxLayout(self); vl.setContentsMargins(24, 20, 24, 20); vl.setSpacing(14)

        # Title row
        tr = QHBoxLayout()
        icon = QLabel("󰂺"); icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background:#1e1030;border-radius:8px;font-size:18px;")
        tr.addWidget(icon)
        ti = QVBoxLayout(); ti.setSpacing(2)
        nm = QLabel(report_name)
        nm.setStyleSheet(f"font-size:16px;font-weight:800;color:{TEXT_WHITE};")
        nm.setWordWrap(True)
        meta = QLabel(f"{rtype}  ·  {date}  ·  {author}")
        meta.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};")
        ti.addWidget(nm); ti.addWidget(meta)
        tr.addLayout(ti, 1)
        vl.addLayout(tr)

        # Divider
        vl.addWidget(sep())

        # Content
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(content)
        vl.addWidget(txt, 1)

        # Footer
        vl.addWidget(sep())
        fr = QHBoxLayout(); fr.setSpacing(10)
        fr.addStretch()
        cl = QPushButton("Close"); cl.setObjectName("close_btn")
        cl.clicked.connect(self.close)
        dl = QPushButton("⬇  Download")
        dl.clicked.connect(lambda: self._fake_download(report_name))
        fr.addWidget(cl); fr.addWidget(dl)
        vl.addLayout(fr)

    def _fake_download(self, name):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Download", f"'{name}' download started.")


#  Add Schedule Dialog 

class AddScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Scheduled Report")
        self.setModal(True); self.setFixedSize(400, 270)
        self.result_data = None
        self.setStyleSheet(f"""
            QDialog {{ background:{BG_CARD2}; }}
            QWidget {{ font-family:'Segoe UI',sans-serif; background:transparent; color:{TEXT_WHITE}; }}
            QLabel  {{ color:{TEXT_WHITE}; }}
            QLineEdit, QComboBox, QTimeEdit {{
                background:#111827; border:1px; border-radius:6px;
                color:{TEXT_WHITE}; font-size:13px; padding:5px 10px;
            }}
            QComboBox::drop-down {{ border:none; }}
            QComboBox QAbstractItemView {{ background:#111827; color:{TEXT_WHITE};
                selection-background-color:{CYAN}; }}
            QPushButton {{
                background:{CYAN}; color:#000; border:none; border-radius:8px;
                font-size:13px; font-weight:700; padding:8px 22px;
            }}
            QPushButton:hover {{ background:#00eeff; }}
            QPushButton#flat {{
                background:{BG_CARD}; color:{TEXT_MUTED};
                border:1px;
            }}
            QPushButton#flat:hover {{ color:{TEXT_WHITE}; }}
        """)

        vl = QVBoxLayout(self); vl.setContentsMargins(24,20,24,20); vl.setSpacing(14)
        ttl = QLabel("New Scheduled Report")
        ttl.setStyleSheet(f"font-size:18px;font-weight:800;color:{TEXT_WHITE};")
        vl.addWidget(ttl)

        form = QFormLayout(); form.setSpacing(10)
        self.name_e = QLineEdit(); self.name_e.setPlaceholderText("e.g. Daily Threat Briefing")
        self.type_cb = QComboBox()
        self.type_cb.addItems(["Executive","Incident","Compliance","Strategic"])
        self.freq_cb = QComboBox()
        self.freq_cb.addItems(["Daily","Weekly (Mon)","Weekly (Fri)","Monthly"])
        self.time_e = QTimeEdit(QTime(8,0)); self.time_e.setDisplayFormat("HH:mm")
        form.addRow("Name:",      self.name_e)
        form.addRow("Type:",      self.type_cb)
        form.addRow("Frequency:", self.freq_cb)
        form.addRow("Run at:",    self.time_e)
        vl.addLayout(form)

        br = QHBoxLayout(); br.setSpacing(10); br.addStretch()
        cn = QPushButton("Cancel"); cn.setObjectName("flat"); cn.clicked.connect(self.reject)
        sv = QPushButton("Save Schedule"); sv.clicked.connect(self._save)
        br.addWidget(cn); br.addWidget(sv)
        vl.addLayout(br)

    def _save(self):
        self.result_data = {
            "name": self.name_e.text() or "Unnamed Report",
            "freq": f"{self.freq_cb.currentText()} at {self.time_e.time().toString('HH:mm')}",
            "next": "Scheduled",
        }
        self.accept()

class GenerateReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GenerateReport")
        self.setModal(True); self.setFixedSize(400,230)
        self.result_data = None
        self.setStyleSheet(f"""
            QDialog {{background:{BG_CARD2};}}
            QWidget {{font-family:'Segoe UI',sans-serif; background:transparent; color:{TEXT_WHITE};}}
            QLabel {{color:{TEXT_WHITE};}}
            QLineEdit, QComboBox{{
               background:#11827; border:1px; border-radius:6px;
               color:{TEXT_WHITE}; font-size:13px; padding:5px 10px;
            }}
        """)
        vl = QVBoxLayout(self); vl.setContentsMargins(24,20,24,20); vl.setSpacing(14)
        ttl = QLabel("Generate New Report")
        ttl.setStyleSheet(f"font-size:18px;font-weight:800; color:{TEXT_WHITE};")
        vl.addWidget(ttl)

        form = QFormLayout(); form.setSpacing(10)
        self.name_e = QLineEdit(); self.name_e.setPlaceholderText("e.g. Daily Security Digest")
        self.type_cb = QComboBox()
        self.type_cb.addItems(["Executive", "Incident", "Compliance", "Strategic"])
        form.addRow("Name:", self.name_e)
        form.addRow("Type:", self.type_cb)
        vl.addLayout(form)

        br = QHBoxLayout(); br.setSpacing(10); br.addStretch()
        cn = QPushButton("Cancel"); cn.setObjectName("flat"); cn.clicked.connect(self.reject)
        gn = QPushButton("Generate"); gn.clicked.connect(self._generate)
        br.addWidget(cn); br.addWidget(gn)
        vl.addLayout(br)

    def _generate(self):
        from datetime import datetime
        name = self.name_e.text().strip() or "Untitled Report"
        self.result_data = (
            name,
            "0.1 MB",
            self.type_cb.currentText(),
            datetime.now().strftime("%b %d, %Y"),
            "Admin",
        )
        self.accept()

# ── Report row widget ──────────────────────────────────────────────────────────
class ReportRow(QWidget):
    def __init__(self, name, size, rtype, date, author, parent=None):
        super().__init__(parent)
        self._name = name
        self.setStyleSheet("background:transparent;")
        self.setMinimumHeight(64)
        self.setMaximumHeight(72)

        hl = QHBoxLayout(self); hl.setContentsMargins(20, 0, 20, 0); hl.setSpacing(0)

        # Red file icon bubble (matches target mockup) 

        ic = QLabel("󰂺"); ic.setFixedSize(34, 34)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(
            "background:#2a1020; border-radius:1px; font-size:12px; "
            "color:#ef5350; border: 1px solid #3d1a28;"
        )
        hl.addWidget(ic)
        hl.addSpacing(12)

        #  Name + size 

        nv = QVBoxLayout(); nv.setSpacing(2)
        n = QLabel(name)
        n.setStyleSheet(f"color:{TEXT_WHITE};font-size:11.5px;font-weight:600;background:transparent;")
        s = QLabel(size)
        s.setStyleSheet(f"color:{TEXT_MUTED};font-size:10px;background:transparent;")
        nv.addWidget(n); nv.addWidget(s)

        # Name column takes the most space — no rigid stretch so it wraps naturally

        nw = QWidget(); nw.setLayout(nv)
        nw.setStyleSheet("background:transparent;")
        nw.setMinimumWidth(140)
        hl.addWidget(nw, 28)
        hl.addSpacing(8)

        #  Type badge — pill shape, no outer border box 

        badge = QLabel(rtype)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(84, 24)
        badge.setStyleSheet(f"""
            color: {TEXT_WHITE};
            background: #1e2d45;
            border: 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        """)
        hl.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        hl.addSpacing(8)

        #  Date 

        dt = QLabel(date)
        dt.setStyleSheet(f"color:{TEXT_MUTED};font-size:11px;background:transparent;")
        dt.setMinimumWidth(90)
        hl.addWidget(dt, 16)

        #  Author 
        au = QLabel(author)
        au.setStyleSheet(f"color:{TEXT_SUB};font-size:12px;background:transparent;")
        au.setMinimumWidth(80)
        hl.addWidget(au, 14)

        #  Actions: View (cyan text) + Download (outlined pill) 

        vb = QPushButton("View")
        vb.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {CYAN}; font-size: 13px; font-weight: 650;
                padding: 1 4px;
            }}
            QPushButton:hover {{ color: #00eeff; }}
        """)
        vb.setCursor(Qt.CursorShape.PointingHandCursor)
        vb.clicked.connect(self._preview)
        vb.setFixedWidth(36)

        db = QPushButton("⬇  Download")
        db.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px;
                border-radius: 7px;
                color: {TEXT_MUTED};
                font-size: 13px;
                font-weight: 650;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                border-color: {CYAN};
                color: {CYAN};
                background: #071520;
            }}
        """)
        db.setCursor(Qt.CursorShape.PointingHandCursor)
        db.setFixedHeight(28)
        db.clicked.connect(self._download)

        ab = QHBoxLayout(); ab.setSpacing(10); ab.setContentsMargins(0,0,0,0)
        ab.addWidget(vb); ab.addWidget(db); ab.addStretch()
        aw = QWidget(); aw.setLayout(ab); aw.setStyleSheet("background:transparent;")
        hl.addWidget(aw, 20)

    def _preview(self):
        dlg = ReportPreviewDialog(self._name, self.window())
        dlg.exec()

    def _download(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        content = ReportPreviewDialog.CONTENT.get(self._name)
        text = content[3] if content else f"No content available for:\n{self._name}"

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", f"{self._name}.txt", "Text Files (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
                QMessageBox.information(self, "Download Complete", f"'{self._name}' saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Download Failed", f"Could not save file:\n{e}")

    def enterEvent(self, e):
        self.setStyleSheet(f"background:{BG_ROW_H}; border-radius:6px;")
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setStyleSheet("background:transparent;")
        super().leaveEvent(e)


# ── Scheduled job card ─────────────────────────────────────────────────────────
def sched_card(name, freq, next_run):
    w = QWidget()
    w.setStyleSheet(f"background:{BG_CARD2};border:1px;border-radius:10px;")
    w.setFixedHeight(76)
    hl = QHBoxLayout(w); hl.setContentsMargins(14,10,14,10); hl.setSpacing(10)
    vl = QVBoxLayout(); vl.setSpacing(3)
    nm = QLabel(name)
    nm.setStyleSheet(f"font-size:15px;font-weight:700;color:{TEXT_WHITE};background:transparent;")
    fr = QLabel(f"󰅐  {freq}")
    fr.setStyleSheet(f"font-size:13px;color:{TEXT_MUTED};background:transparent;")
    nr = QLabel(f"Next run: {next_run}")
    nr.setStyleSheet(f"font-size:13px;color:{TEXT_MUTED};background:transparent;")
    vl.addWidget(nm); vl.addWidget(fr); vl.addWidget(nr)
    hl.addLayout(vl, 1)
    badge = QLabel("ACTIVE")
    badge.setStyleSheet(f"""
        color:{GREEN_ACT};background:#0d2018;border:1px solid {GREEN_ACT};
        border-radius:5px;padding:2px 8px;font-size:13px;font-weight:800;
    """)
    hl.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
    return w


#  CARD: Header bar (title + Generate Report button) 

class HeaderBar(QWidget):
    """Top-of-page title, subtitle, and the 'Generate Report' action button."""
    def __init__(self, parent=None):
        super().__init__(parent)
        hl = QHBoxLayout(self); hl.setContentsMargins(0, 0, 0, 0)

        vl = QVBoxLayout(); vl.setSpacing(3)
        t = QLabel("Security Reports")
        t.setStyleSheet(f"font-size:22px;font-weight:800;color:{TEXT_WHITE};background:transparent;")
        s = QLabel("Generate, schedule, and manage security documentation")
        s.setStyleSheet(f"font-size:18px;color:{TEXT_MUTED};background:transparent;")
        vl.addWidget(t); vl.addWidget(s)
        hl.addLayout(vl); hl.addStretch()

        self.generate_btn = QPushButton(" 󰂺 Generate Report")
        self.generate_btn.setStyleSheet(f"""
            QPushButton {{ background:{CYAN};color:#000;border:none;border-radius:8px;
                           font-size:13px;font-weight:700;padding:10px 22px; }}
            QPushButton:hover {{ background:#00eeff; }}
        """)
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hl.addWidget(self.generate_btn)


#  CARD: A single top-row stat tile (Reports Generated / Scheduled Jobs / etc.) 

class StatCard(QFrame):
    """One of the three small stat tiles at the top of the page."""
    def __init__(self, icon, icon_color, label, value, sub_label, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card_frame")
        # Use QFrame with explicit stylesheet scoped to objectName so global
        # QWidget rules in PAGE_STYLE cannot bleed through and flatten the card.
        self.setStyleSheet(f"""
            QFrame#stat_card_frame {{
                background: {BG_CARD};
                border: 1px;
                border-radius: 16px;
            }}
            QFrame#stat_card_frame QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self.setMinimumHeight(88)

        cl = QHBoxLayout(self); cl.setContentsMargins(18, 14, 18, 14); cl.setSpacing(16)

        # Icon bubble — coloured background matching the design mockup

        ic = QLabel(icon); ic.setFixedSize(48, 48)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(f"background:#1a2540;border-radius:12px;font-size:22px;border:none;")
        cl.addWidget(ic)

        info = QVBoxLayout(); info.setSpacing(2)
        lb = QLabel(label.upper())
        lb.setStyleSheet(f"color:{TEXT_MUTED};font-size:10px;letter-spacing:1px;font-weight:600;")
        vn = QLabel(value)
        vn.setStyleSheet(f"color:{TEXT_WHITE};font-size:28px;font-weight:800;")
        sb = QLabel(sub_label)
        sb.setStyleSheet(f"color:{TEXT_MUTED};font-size:11px;")
        info.addWidget(lb); info.addWidget(vn); info.addWidget(sb)
        cl.addLayout(info, 1)


class StatCardsRow(QWidget):
    """The full row of three stat tiles, wired with NovaSphere's current numbers."""
    STATS = [
        ("󰄬", CYAN,     "Reports Generated", "142",   "This month"),
        ("󰅐", BLUE_A,   "Scheduled Jobs",    "8",     "Active schedules"),
        ("󰇮",  PURPLE_A, "Auto-Delivered",    "1,024", "Recipients reached"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self.setFixedHeight(100)
        hl = QHBoxLayout(self); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(16)
        for icon, color, label, val, sub in self.STATS:
            card = StatCard(icon, color, label, val, sub)
            hl.addWidget(card, 1)


# ─ CARD: Report Archive (search, column headers, rows, View All Archive) 

class ReportArchiveCard(QFrame):
    """
    Self-contained Report Archive card: search box, filter button, column
    headers, the report rows themselves, and the View All / Show Less toggle.

    Pass an initial list of (name, size, type, date, author) tuples; the card
    owns its own filtering/show-all state from then on.
    """
    def __init__(self, reports, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG_CARD};border:1px;border-radius:16px;")
        self._all = list(reports)
        self._shown = list(reports)
        self._show_all = False

        vl = QVBoxLayout(self); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # -- header row (title, search, filter dropdown) --------------------
        self._active_filter = "All"   # track current type filter

        hdr_w = QWidget()
        hdr_w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        hdr = QHBoxLayout(hdr_w); hdr.setContentsMargins(18, 14, 18, 10); hdr.setSpacing(10)
        ttl = QLabel(" 󰂺  Report Archive")
        ttl.setStyleSheet(f"font-size:17px;font-weight:700;color:{TEXT_WHITE};background:transparent;")
        hdr.addWidget(ttl); hdr.addStretch()

        self._srch = QLineEdit(); self._srch.setPlaceholderText("Search reports...")
        self._srch.setFixedWidth(180)
        self._srch.textChanged.connect(self._apply_filters)
        hdr.addWidget(self._srch)

        # Filter dropdown — QComboBox styled to match the dark UI

        self._filter_cb = QComboBox()
        self._filter_cb.addItems(["All", "Executive", "Incident", "Compliance", "Strategic"])
        self._filter_cb.setFixedHeight(32)
        self._filter_cb.setMinimumWidth(110)
        self._filter_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._filter_cb.setStyleSheet(f"""
            QComboBox {{
                background: #111827;
                border: 1px solid {BORDER};
                border-radius: 7px;
                color: {TEXT_WHITE};
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QComboBox:hover {{
                border-color: {CYAN};
                color: {CYAN};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 22px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0; height: 0;
                border-left:  4px solid transparent;
                border-right: 4px solid transparent;
                border-top:   5px solid {TEXT_MUTED};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: #111827;
                border: 1px solid {BORDER};
                border-radius: 8px;
                color: {TEXT_WHITE};
                selection-background-color: {CYAN};
                selection-color: #000;
                padding: 4px;
                outline: none;
            }}
        """)
        self._filter_cb.currentTextChanged.connect(self._on_filter_changed)
        hdr.addWidget(self._filter_cb)

        vl.addWidget(hdr_w)
        vl.addWidget(sep())

        #  column header labels 

        col_w = QWidget()
        col_w.setFixedHeight(28)
        col_w.setStyleSheet("background:transparent;")
        col_w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        col = QHBoxLayout(col_w); col.setContentsMargins(66, 6, 20, 6); col.setSpacing(0)
        # Stretch values mirror the ReportRow layout proportions
        for txt, stretch in [("REPORT NAME", 25), ("TYPE", 10), ("DATE GENERATED", 16), ("AUTHOR", 15), ("ACTIONS", 21)]:
            lb = QLabel(txt)
            lb.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;letter-spacing:1px;background:transparent;")
            lb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            col.addWidget(lb, stretch)
        vl.addWidget(col_w)
        vl.addWidget(sep())

        #  rows container 

        self._rows_w = QWidget()
        self._rows_w.setStyleSheet("background:transparent;")
        self._rows_w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._rows_vl = QVBoxLayout(self._rows_w)
        self._rows_vl.setContentsMargins(0, 0, 0, 0); self._rows_vl.setSpacing(0)
        self._rebuild_rows()
        vl.addWidget(self._rows_w)
        vl.addWidget(sep())

        #  "View All Archive" / "Show Less" toggle 

        self._va_btn = QPushButton("View All Archive")
        self._va_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent;border:none;color:{TEXT_MUTED};
                           font-size:13px;padding:12px; }}
            QPushButton:hover {{ color:{CYAN}; }}
        """)
        self._va_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._va_btn.clicked.connect(self._toggle_all)
        vl.addWidget(self._va_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        vl.addStretch(1)

    def _rebuild_rows(self):
        while self._rows_vl.count():
            item = self._rows_vl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rows = self._shown if self._show_all else self._shown[:4]
        for i, r in enumerate(rows):
            self._rows_vl.addWidget(ReportRow(*r))
            if i < len(rows) - 1:
                self._rows_vl.addWidget(sep())

    def _on_filter_changed(self, value):
        self._active_filter = value
        self._apply_filters()

    def _apply_filters(self):
        q = self._srch.text().strip().lower()
        result = list(self._all)
        # Type filter
        if self._active_filter != "All":
            result = [r for r in result if r[2].lower() == self._active_filter.lower()]
        # Text search across name, type, author
        if q:
            result = [r for r in result
                      if q in r[0].lower() or q in r[2].lower() or q in r[4].lower()]
        self._shown = result
        self._rebuild_rows()

    def _toggle_all(self):
        self._show_all = not self._show_all
        self._va_btn.setText("Show Less" if self._show_all else "View All Archive")
        self._rebuild_rows()

    def add_report(self, report_tuple):
        """Insert a newly generated report at the top of the archive."""
        self._all.insert(0, report_tuple)
        self._shown.insert(0, report_tuple)
        self._rebuild_rows()


#  CARD: Incident Analysis (donut chart + threat breakdown + templates) 

class IncidentAnalysisCard(QFrame):
    """Donut chart of incident types plus the three clickable report templates."""
    BREAKDOWN = [
        (RED,      "Ransomware",     "34%"),
        (ORANGE,   "Phishing",       "28%"),
        (BLUE_A,   "Insider Threat", "20%"),
        (GREEN_A,  "Malware",        "12%"),
        (PURPLE_A, "Other",           "6%"),
    ]
    TEMPLATES = ["Executive Security Summary", "Detailed Incident Log", "Compliance Audit (GDPR/ISO)"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG_CARD};border:1px;border-radius:16px;")
        vl = QVBoxLayout(self); vl.setContentsMargins(18, 14, 18, 16); vl.setSpacing(10)

        ttl = QLabel(" 󰐟 Incident Analysis")
        ttl.setStyleSheet(f"font-size:15px;font-weight:700;color:{TEXT_WHITE};background:transparent;")
        vl.addWidget(ttl)

        donut = DonutChart()
        vl.addWidget(donut, alignment=Qt.AlignmentFlag.AlignHCenter)

        for color, label, pct in self.BREAKDOWN:
            row = QHBoxLayout(); row.setSpacing(8)
            dot = QLabel("●"); dot.setStyleSheet(f"color:{color};font-size:13px;background:transparent;")
            lb = QLabel(label); lb.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;background:transparent;")
            pc = QLabel(pct); pc.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;font-weight:700;background:transparent;")
            row.addWidget(dot); row.addWidget(lb, 1); row.addWidget(pc)
            vl.addLayout(row)

        vl.addSpacing(4); vl.addWidget(sep())

        sub = QLabel("AVAILABLE TEMPLATES")
        sub.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;letter-spacing:2px;background:transparent;")
        vl.addWidget(sub)

        self.template_buttons = {}
        for tpl in self.TEMPLATES:
            b = QPushButton(f"  {tpl}   ›")
            b.setStyleSheet(f"""
                QPushButton {{ background:{BG_CARD2};border:1px solid {BORDER};border-radius:8px;
                               color:{TEXT_WHITE};font-size:12px;text-align:left;padding:9px 12px; }}
                QPushButton:hover {{ border-color:{CYAN};color:{CYAN}; }}
            """)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            vl.addWidget(b)
            self.template_buttons[tpl] = b


#  CARD: a single scheduled-job row inside the Scheduled card 

class ScheduledJobCard(QWidget):
    """One scheduled-report row: name, frequency, next run, and an ACTIVE badge."""
    def __init__(self, name, freq, next_run, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG_CARD2};border:1px;border-radius:10px;")
        self.setFixedHeight(76)
        hl = QHBoxLayout(self); hl.setContentsMargins(14, 10, 14, 10); hl.setSpacing(10)

        vl = QVBoxLayout(); vl.setSpacing(3)
        nm = QLabel(name)
        nm.setStyleSheet(f"font-size:14px;font-weight:700;color:{TEXT_WHITE};background:transparent;")
        fr = QLabel(f" 󱑃 {freq}")
        fr.setStyleSheet(f"font-size:11px;color:{TEXT_MUTED};background:transparent;")
        nr = QLabel(f"Next run: {next_run}")
        nr.setStyleSheet(f"font-size:11px;color:{TEXT_MUTED};background:transparent;")
        vl.addWidget(nm); vl.addWidget(fr); vl.addWidget(nr)
        hl.addLayout(vl, 1)

        badge = QLabel("ACTIVE")
        badge.setStyleSheet(f"""
            color:{GREEN_ACT};background:#0d2018;border:1px solid {GREEN_ACT};
            border-radius:5px;padding:2px 8px;font-size:10px;font-weight:800;
        """)
        hl.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)


#  CARD: Scheduled (header + Add button + list of ScheduledJobCard rows) 

class ScheduledCard(QFrame):
    """Scheduled-reports card: '+ Add' button opens AddScheduleDialog."""
    def __init__(self, schedules, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG_CARD};border:1px;border-radius:16px;")
        self._schedules = list(schedules)

        vl = QVBoxLayout(self); vl.setContentsMargins(18, 14, 18, 14); vl.setSpacing(10)

        hl = QHBoxLayout()
        ttl = QLabel(" 󰸘  Scheduled")
        ttl.setStyleSheet(f"font-size:15px;font-weight:700;color:{TEXT_WHITE};background:transparent;")
        hl.addWidget(ttl); hl.addStretch()

        self.add_btn = QPushButton("+ Add")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent;border:none;color:{CYAN};
                           font-size:15px;font-weight:700;padding:0; }}
            QPushButton:hover {{ color:#00eeff; }}
        """)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_schedule)
        hl.addWidget(self.add_btn)
        vl.addLayout(hl)

        self._sched_vl = QVBoxLayout(); self._sched_vl.setSpacing(8)
        self._rebuild()
        vl.addLayout(self._sched_vl)

    def _rebuild(self):
        while self._sched_vl.count():
            item = self._sched_vl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in self._schedules:
            self._sched_vl.addWidget(ScheduledJobCard(s["name"], s["freq"], s["next"]))

    def _add_schedule(self):
        dlg = AddScheduleDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_data:
            self._schedules.append(dlg.result_data)
            self._rebuild()


#  CARD: Compliance Score (title + four ComplianceBar rows) 

class ComplianceScoreCard(QFrame):
    """Compliance Score card: HIPAA / GDPR / PCI-DSS / SOC2 progress bars."""
    SCORES = [("HIPAA", 91), ("GDPR", 84), ("PCI-DSS", 73), ("SOC2", 88)]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG_CARD};border:1px;border-radius:16px;")
        vl = QVBoxLayout(self); vl.setContentsMargins(18, 14, 18, 14); vl.setSpacing(10)
        ttl = QLabel("󰒃  Compliance Score")
        ttl.setStyleSheet(f"font-size:15px;font-weight:700;color:{TEXT_WHITE};background:transparent;")
        vl.addWidget(ttl)
        for label, pct in self.SCORES:
            vl.addWidget(ComplianceBar(label, pct))


#  Right-hand column: stacks Incident Analysis / Scheduled / Compliance 

class RightColumn(QWidget):
    def __init__(self, schedules, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(self); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(16)
        self.incident_card = IncidentAnalysisCard()
        self.scheduled_card = ScheduledCard(schedules)
        self.compliance_card = ComplianceScoreCard()
        vl.addWidget(self.incident_card)
        vl.addWidget(self.scheduled_card)
        vl.addWidget(self.compliance_card)


#  Main Reports Page 

class ReportsPage(QWidget):
    """
    Assembles the separated cards above into the full Security Reports page:
    HeaderBar -> StatCardsRow -> [ReportArchiveCard | RightColumn].
    """

    REPORTS = [
        ("Weekly Executive Summary",     "2.4 MB", "Executive",  "May 15, 2025", "System (Auto)"),
        ("Ransomware Incident Analysis", "1.1 MB", "Incident",   "May 14, 2025", "Admin"),
        ("User Activity Audit - Finance","4.8 MB", "Compliance", "May 12, 2025", "J. Doe"),
        ("Monthly Threat Landscape",     "5.2 MB", "Strategic",  "May 01, 2025", "System (Auto)"),
    ]

    SCHEDULES = [
        {"name": "Daily Threat Briefing",    "freq": "Daily at 08:00", "next": "Tomorrow, 08:00"},
        {"name": "Weekly Compliance Check",  "freq": "Weekly (Mon)",   "next": "May 19, 09:00"},
    ]

    # Maps the "AVAILABLE TEMPLATES" button labels (in IncidentAnalysisCard)
    # to a report name that already has preview content in
    # ReportPreviewDialog.CONTENT, so clicking a template opens a real preview.
    TEMPLATE_MAP = {
        "Executive Security Summary":   "Weekly Executive Summary",
        "Detailed Incident Log":        "Ransomware Incident Analysis",
        "Compliance Audit (GDPR/ISO)":  "User Activity Audit - Finance",
    }

    def __init__(self, navigate_callback=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(PAGE_STYLE)
        self._navigate = navigate_callback  # optional hook; unused internally

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        body = QWidget()
        body.setStyleSheet(f"background:{BG_MAIN};")
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(30, 24, 30, 30); root.setSpacing(20)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # -- header ----------------------------------------------------------
        self.header = HeaderBar()
        root.addWidget(self.header)
        self.header.generate_btn.clicked.connect(self._on_generate_report)

        # -- stat cards ----------------------------------------------------
        self.stat_cards = StatCardsRow()
        root.addWidget(self.stat_cards)

        # -- body row: archive (left) + right column (incident/scheduled/compliance) --
        body_row = QHBoxLayout(); body_row.setSpacing(20)
        self.archive_card = ReportArchiveCard(self.REPORTS)
        self.right_column = RightColumn(self.SCHEDULES)
        body_row.addWidget(self.archive_card, 55)
        body_row.addWidget(self.right_column, 42)
        root.addLayout(body_row)

        # Wire the three template buttons in Incident Analysis to navigate
        for tpl_name, btn in self.right_column.incident_card.template_buttons.items():
            btn.clicked.connect(lambda _, n=tpl_name: self._on_template_clicked(n))

    # -- actions -----------------------------------------------------------
    def _on_template_clicked(self, template_name):
        report_name = self.TEMPLATE_MAP.get(template_name, template_name)
        dlg = ReportPreviewDialog(report_name, self)
        dlg.exec()

        if self._navigate:
            self._navigate(f"reports.template:{template_name}")

    def _on_generate_report(self):
        dlg = GenerateReportDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_data:
            self.archive_card.add_report(dlg.result_data)

# ── Standalone preview ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("NovaSphere — Security Reports")
    win.setMinimumSize(1200, 760); win.resize(1400, 860)
    win.setStyleSheet(f"QMainWindow,QWidget{{background:{BG_MAIN};}}")
    win.setCentralWidget(ReportsPage())
    win.show()
    sys.exit(app.exec())