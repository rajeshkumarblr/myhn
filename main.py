import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gemini_station import GeminiBrowser

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
    app = QApplication(sys.argv)
    app.setApplicationName("Gemini Station")
    
    window = GeminiBrowser()
    
    # 1. Start Maximized
    window.showMaximized()
    
    sys.exit(app.exec())
