# HN Station

A focused, lightweight desktop wrapper for Hacker News.

## What it is
This is a dedicated Hacker News desktop app built with Python + PyQt6 WebEngine, so you can read HN in a distraction-free window (separate from your main browser) with tabs, session persistence, and keyboard shortcuts.

## Screenshot

![HN Station Screenshot](assets/screenshot.png)

## Key Features
- **Tabs**: Open links in new tabs.
- **New Tab shortcut**: `Ctrl+T` opens a new tab to Hacker News.
- **Address bar**: Type a URL and press Enter to navigate.
- **Address bar focus**: `Ctrl+L` or `Alt+D` focuses the URL box.
- **Progress indicator**: Shows page load progress in the status bar.
- **Session Restore**: Remembers open tabs across restarts.
- **Lightweight**: Python + PyQt6 (no Electron).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rajeshkumarblr/myhn.git
    cd myhn
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python main.py
    ```

## Requirements
- Python 3.8+
- PyQt6
- PyQt6-WebEngine

## Building the Executable

To build a standalone Windows executable (`.exe`):

1.  Open PowerShell in the project directory.
2.  Run the build script:
    ```powershell
    .\build.ps1
    ```
3.  The executable will be created at `dist/windows/hnapp.exe`.

