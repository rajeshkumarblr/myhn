# Gemini Station

A dedicated, persistent desktop workspace for Google Gemini.

## The Problem
Browser clutter and context switching kill developer focus. Keeping your AI assistant in a browser tab among dozens of others leads to distraction and lost context.

## The Solution
**Gemini Station** is a dedicated, lightweight (Python-based) AI cockpit. It provides a focused environment for interacting with Google Gemini, separate from your main browser.

## Key Features
- **Persistent Login**: Maintains your session so you don't have to log in every time.
- **Custom User Agents**: Optimized for the best Gemini experience.
- **Lightweight**: Built with Python and PyQt6, avoiding the overhead of Electron.
- **Distraction-Free**: Clean interface with custom context menus and tab management.
- **Session Restoration**: Remembers your open tabs and active chat.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rajeshkumarblr/gemini_station.git
    cd gemini_station
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
3.  The executable will be created at `dist/windows/GeminiStation.exe`.

