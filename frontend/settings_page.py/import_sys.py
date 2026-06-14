import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSlider,
    QCheckBox
)
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)

# Main Window
window = QWidget()
window.setWindowTitle("System Configuration")
window.resize(1200, 700)

# Dark Theme
window.setStyleSheet("""
QWidget{
    background-color:#081A2E;
    color:white;
    font-family:Segoe UI;
}

QPushButton{
    background-color:#123456;
    border-radius:8px;
    padding:10px;
    color:white;
}

QPushButton:hover{
    background-color:#1E4D80;
}

QCheckBox{
    font-size:14px;
}
""")

# Main Layout
main_layout = QHBoxLayout()

# ---------------- Sidebar ----------------
sidebar = QVBoxLayout()

btn1 = QPushButton("Detection & Response")
btn2 = QPushButton("File Monitoring")
btn3 = QPushButton("User Management")
btn4 = QPushButton("Alerts & Notifications")
btn5 = QPushButton("System & Performance")

sidebar.addWidget(btn1)
sidebar.addWidget(btn2)
sidebar.addWidget(btn3)
sidebar.addWidget(btn4)
sidebar.addWidget(btn5)
sidebar.addStretch()

# ---------------- Content ----------------
content = QVBoxLayout()

title = QLabel("System Configuration")
title.setStyleSheet("font-size:28px; font-weight:bold;")

subtitle = QLabel(
    "Manage security policies, users, and system preferences"
)

content.addWidget(title)
content.addWidget(subtitle)

# Heuristic Sensitivity
heuristic = QLabel("⚡ Heuristic Sensitivity")
heuristic.setStyleSheet("font-size:20px; font-weight:bold;")

content.addWidget(heuristic)

slider_label = QLabel("Detection Threshold")

slider = QSlider(Qt.Horizontal)
slider.setValue(50)

content.addWidget(slider_label)
content.addWidget(slider)

content.addWidget(QLabel("Balanced (Recommended)"))

# Automated Response
response = QLabel("🔒 Automated Response")
response.setStyleSheet("font-size:20px; font-weight:bold;")

content.addWidget(response)

cb1 = QCheckBox("Active Defense Engine")
cb1.setChecked(True)

cb2 = QCheckBox("Kill Suspicious Processes")
cb2.setChecked(True)

cb3 = QCheckBox("Isolate Compromised Hosts")

content.addWidget(cb1)
content.addWidget(cb2)
content.addWidget(cb3)

content.addStretch()

save_btn = QPushButton("Save Changes")
content.addWidget(save_btn)

# Add layouts
main_layout.addLayout(sidebar, 1)
main_layout.addLayout(content, 4)

window.setLayout(main_layout)

window.show()

sys.exit(app.exec_())