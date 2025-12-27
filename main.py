import sys
import os
import argparse
import traceback

# --- 1. PERFORMANCE FLAGS (Must be set before QApplication) ---
# Unlocks the GPU for smooth 60FPS scrolling
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist"

from PyQt6.QtWidgets import QApplication, QMessageBox
from src.hn_station import HNBrowser, APP_NAME

def main():
    # --- 2. ARGUMENT PARSING (Future Proofing) ---
    parser = argparse.ArgumentParser(description="HN Station - The Hacker's Browser")
    parser.add_argument("--debug", action="store_true", help="Enable verbose console logging")
    parser.add_argument("--reset", action="store_true", help="Reset session and cookies on startup")
    args = parser.parse_args()

    # --- 3. APP LAUNCH ---
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        
        # Pass args to the browser if you want to use them later
        # e.g., if args.reset: os.remove(session_file)
        window = HNBrowser()
        window.showMaximized()
        
        sys.exit(app.exec())
    
    except Exception as e:
        # --- 4. GLOBAL CRASH HANDLER ---
        # If the app crashes, this saves the error to a file so you can debug it.
        error_msg = f"Fatal Error:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_msg)
        with open("crash_log.txt", "w") as f:
            f.write(error_msg)
        # Attempt to show a popup if Qt is still alive
        try:
            QMessageBox.critical(None, "HN Station Crashed", f"Detailed error saved to crash_log.txt\n\n{str(e)}")
        except:
            pass

if __name__ == "__main__":
    main()