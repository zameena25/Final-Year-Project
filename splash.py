# frontend / splash.py

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer
from pathlib import Path

def show_splash(app: QApplication) -> QSplashScreen:
    logo_path = Path(__file__).parent / "novasphere.png"
    if logo_path.exists():
        pixmap = QPixmap(str(logo_path))
    else:
        pixmap = QPixmap(400, 400)
        pixmap.fill(QColor("#0d1117"))

    splash = QSplashScreen(pixmap)
    splash.showMessage(
        "NOVASPHERE - Loading...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        QColor("#e8eaf0")
    )
    splash.show()
    app.processEvents() #force it to paint immediately
    return splash