# HN Station 🍊

**The Browser for the 1%.**
A dedicated, keyboard-centric reading environment for Hacker News, built with Python & PyQt6.

![HN Station Screenshot](assets/screenshot.png)

## Why use this?
Browser tabs are where productivity goes to die. 

**HN Station** isolates your reading list from your Gmail/Jira clutter. It treats Hacker News threads as "Contexts," not just tabs.

* **No Electron**: Uses Qt6 WebEngine. RAM efficient.
* **No Tracking**: No Google login, no telemetry, no history syncing.
* **Polite**: Built-in rate limiting and retry logic to respect HN's API.

## ⚡ Key Features

### 🚀 Smart "Dual Open"
Right-click any story on the home page and select **"Open Article & Comments"**. 
* Opens the article immediately.
* Loads the HN comments in the background (delayed to prevent rate-limiting).
* **Auto-Grouping**: The Article and Comments share the same **Color Code** and are placed next to each other.

### 🎨 Visual Contexts
Tabs are automatically color-coded by "Thread."
* **Root Page**: Always 🍊 Orange.
* **Threads**: Opening a link starts a new "Color Group." All child tabs (comments, external links) inherit that color.
* Never lose track of which comments belong to which article again.

### ⌨️ Vim-Style Navigation
Navigate feeds without touching the mouse.
* `j` : Scroll Down
* `k` : Scroll Up
* `Ctrl+T` : New Tab
* `Ctrl+W` : Close Tab
* `Ctrl+L` : Focus Address Bar

### 💾 Smart Session Restore
* **Crash Proof**: Saves your open tabs every 5 seconds.
* **Focus Reset**: On restart, it automatically finds and focuses the "Home" tab so you can start fresh, while keeping your reading queue open in the background.

## Installation

### Option 1: The Installer (Windows)
Download the latest `HNStation-Setup.exe` from the releases page.

### Option 2: Run from Source

1.  **Clone:**
    ```bash
    git clone [https://github.com/rajeshkumarblr/myhn.git](https://github.com/rajeshkumarblr/myhn.git)
    cd myhn
    ```

2.  **Install:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run:**
    ```bash
    python main.py
    ```

## Tech Stack
* **Core**: Python 3.10+
* **GUI**: PyQt6 (Qt 6.4+)
* **Engine**: QtWebEngine (Chromium)

---
*Built for the hackers, by a hacker.*