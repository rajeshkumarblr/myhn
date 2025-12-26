import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.hn_station import HNBrowser

APP_NAME = "HN Station"

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = HNBrowser()
    window.showMaximized()
    sys.exit(app.exec())