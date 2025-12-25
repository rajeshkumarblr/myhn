import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.gemini_station import GeminiBrowser, get_asset_path

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
    app = QApplication(sys.argv)
    app.setApplicationName("Gemini Station")
    
    # Set Application Icon (Important for Taskbar/Window Icon)
    icon_path = get_asset_path("gemini.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = GeminiBrowser()
    
    # 1. Start Maximized
    window.showMaximized()
    
    sys.exit(app.exec())
