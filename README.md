# HN App

A focused, lightweight desktop wrapper for Hacker News.

## What it is
This is a dedicated Hacker News browser built with Python + PyQt6 WebEngine, so you can read HN in a distraction-free window (separate from your main browser) with tab support and session persistence.

## Key Features
- **Tabs**: Open links in new tabs.
- **Session Restore**: Remembers open tabs across restarts.
- **Dark Mode**: Toggle a dark theme for reading.
- **Lightweight**: Python + PyQt6 (no Electron).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
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

