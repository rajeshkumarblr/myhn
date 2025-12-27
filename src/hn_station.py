import sys
import os
import json
import time
import urllib.request
import random
import logging
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QToolBar, QStatusBar, QWidget, QStyle, QLineEdit, QProgressBar,
                             QSizePolicy, QMenu)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, 
                                   QWebEngineSettings, QWebEngineScript)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut, QColor
from PyQt6.QtCore import QUrl, QTimer, QSize, QThread, pyqtSignal, Qt

# --- CONFIGURATION ---
APP_NAME = "HN Station"
HOME_URL = "https://news.ycombinator.com/"
PROFILE_NAME = "HN_Profile"

# Expanded High-Contrast Palette (20 Colors)
GROUP_COLORS = [
    QColor("#C62828"), # Red
    QColor("#1565C0"), # Blue
    QColor("#2E7D32"), # Green
    QColor("#EF6C00"), # Orange
    QColor("#6A1B9A"), # Purple
    QColor("#00838F"), # Teal
    QColor("#AD1457"), # Pink
    QColor("#4E342E"), # Brown
    QColor("#37474F"), # Blue Grey
    QColor("#9E9D24"), # Lime
    QColor("#F9A825"), # Yellow-Orange
    QColor("#283593"), # Indigo
    QColor("#4527A0"), # Deep Purple
    QColor("#00695C"), # Teal Green
    QColor("#D84315"), # Deep Orange
    QColor("#424242"), # Grey
    QColor("#0277BD"), # Light Blue
    QColor("#9C27B0"), # Magenta
    QColor("#558B2F"), # Light Green
    QColor("#8D6E63"), # Light Brown
]

# --- HELPER FUNCTIONS ---
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_user_data_path():
    base_path = os.getenv('LOCALAPPDATA') 
    app_path = os.path.join(base_path, APP_NAME)
    if not os.path.exists(app_path):
        os.makedirs(app_path)
    return app_path

def get_asset_path(filename):
    return os.path.join(get_base_path(), "assets", filename)

def get_data_path(filename):
    return os.path.join(get_user_data_path(), filename)

# --- LOGGING SETUP ---
def setup_logging():
    log_file = get_data_path("app.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    sys.stderr = open(log_file, 'a')

# --- SMART CURATOR THREAD (DISABLED FOR NOW) ---
class HNCurator(QThread):
    status_update = pyqtSignal(str, bool)

    def __init__(self, data_path, keywords):
        super().__init__()
        self.data_path = data_path
        self.keywords = [k.lower() for k in keywords]
        self.seen_ids = set()

    def fetch_with_retry(self, url, retries=3):
        for i in range(retries):
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    return json.loads(response.read().decode())
            except Exception as e:
                if i == retries - 1: 
                    logging.warning(f"Failed to fetch {url} after {retries} attempts: {e}")
                    raise e
                time.sleep(1 * (i + 1))
        return None

    def run(self):
        try:
            curated_file = os.path.join(self.data_path, "my_hn_links.json")
            existing_data = []
            if os.path.exists(curated_file):
                with open(curated_file, 'r') as f:
                    existing_data = json.load(f)
                    self.seen_ids = {item['id'] for item in existing_data}

            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            top_ids = self.fetch_with_retry(url)[:60]

            new_finds = []
            for hn_id in top_ids:
                if hn_id in self.seen_ids: continue
                
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{hn_id}.json"
                try:
                    story = self.fetch_with_retry(item_url)
                except:
                    continue

                if not story: continue
                
                title = story.get('title', '').lower()
                matched_keyword = next((k for k in self.keywords if k in title), None)
                if matched_keyword:
                    entry = {
                        "id": hn_id,
                        "title": story.get('title'),
                        "url": story.get('url', f"https://news.ycombinator.com/item?id={hn_id}"),
                        "matched": matched_keyword,
                        "found_at": datetime.now().isoformat()
                    }
                    new_finds.append(entry)
                    self.seen_ids.add(hn_id)
                
                # FIX: 0.5s Delay to prevent 429 Throttling
                time.sleep(0.5) 

            if new_finds:
                updated_data = new_finds + existing_data
                with open(curated_file, 'w') as f:
                    json.dump(updated_data, f, indent=2)
                self.status_update.emit(f"🍊 Curator found {len(new_finds)} new stories!", False)
        except Exception as e:
            logging.error(f"Curator Error: {e}")

# --- CUSTOM PAGE & VIEW ---
class HNPage(QWebEnginePage):
    def __init__(self, profile, main_window):
        super().__init__(profile, main_window)
        self.main_window = main_window

    def createWindow(self, _type):
        parent_view = self.view()
        parent_color = parent_view.group_color if hasattr(parent_view, 'group_color') else None
        return self.main_window.add_new_tab(url=None, forced_color=parent_color)

class HNView(QWebEngineView):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.group_color = QColor("#000000")
        self.content_type = ""
        self.retries = 0 # Safety counter for auto-retry

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        
        # Only show Dual Open on HN List Pages
        current_url = self.url().toString()
        is_hn_list = "news.ycombinator.com" in current_url and "item?id=" not in current_url

        dual_action = QAction("Open Article & Comments", self)
        dual_action.triggered.connect(self.extract_and_open_dual)
        
        open_action = QAction("Open Link in New Tab", self)
        open_action.triggered.connect(self.extract_and_open)
        
        copy_action = QAction("Copy Link Address", self)
        copy_action.triggered.connect(self.extract_and_copy)
        
        first = menu.actions()[0] if menu.actions() else None
        if first:
            if is_hn_list:
                menu.insertAction(first, dual_action)
            
            menu.insertAction(first, open_action)
            menu.insertAction(first, copy_action)
            menu.insertSeparator(first)
        menu.exec(event.globalPos())

    def get_hovered_url_js(self):
        return """
        (function() {
            var path = window._lastClickPath;
            if (!path || path.length === 0) return "";
            for (var i = 0; i < Math.min(path.length, 5); i++) {
                var el = path[i];
                if (el.tagName === 'A' && el.href) return el.href;
            }
            return "";
        })();
        """

    def get_dual_urls_js(self):
        return """
        (function() {
            var path = window._lastClickPath;
            if (!path) return null;
            var anchor = null;
            for (var i = 0; i < Math.min(path.length, 5); i++) {
                if (path[i].tagName === 'A' && path[i].href) { anchor = path[i]; break; }
            }
            if (!anchor) return null;
            var row = anchor.closest('.athing');
            if (row && row.id) {
                return {
                    article: anchor.href,
                    comments: "https://news.ycombinator.com/item?id=" + row.id
                };
            }
            return null;
        })();
        """
    
    def extract_and_open(self):
        self.page().runJavaScript(self.get_hovered_url_js(), self.handle_open)

    def extract_and_open_dual(self):
        self.page().runJavaScript(self.get_dual_urls_js(), self.handle_dual_open)

    def extract_and_copy(self):
        self.page().runJavaScript(self.get_hovered_url_js(), lambda u: QApplication.clipboard().setText(u) if u else None)

    def handle_open(self, url):
        if url: self.main_window.add_new_tab(url)

    def handle_dual_open(self, data):
        if data and isinstance(data, dict):
            self.main_window.open_dual_tabs(data.get('article'), data.get('comments'))

# --- MAIN WINDOW ---
class HNBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        
        setup_logging()
        logging.info("Starting HN Station...")

        self.color_index = 0
        
        icon_path = get_asset_path("hn.ico") 
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        profile_path = get_data_path("web_profile")
        self.profile = QWebEngineProfile(PROFILE_NAME, self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.inject_scripts()

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        
        # --- CHROME STYLE TABS ---
        self.tabs.setUsesScrollButtons(False)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
        
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.handle_tab_change)
        
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        
        self.setCentralWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.setup_toolbar()
        self.setup_shortcuts()

        QTimer.singleShot(100, self.post_init_setup)
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_session)
        self.save_timer.start(5000)

    def get_next_group_color(self):
        color = GROUP_COLORS[self.color_index % len(GROUP_COLORS)]
        self.color_index += 1
        return color

    def setup_toolbar(self):
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f6f6ef; }
            QToolBar { 
                background: #f6f6ef; 
                border-bottom: 2px solid #ff6600; 
                spacing: 5px; 
                padding: 5px; 
            }
            QToolButton { 
                background: transparent; border: none; padding: 4px; color: #333; 
            }
            QToolButton:hover { background: #e5e5e5; border-radius: 4px; }
            QLineEdit { 
                border: 1px solid #ccc; border-radius: 3px; padding: 4px; 
                background: #fff; selection-background-color: #ff6600; color: #000;
            }
            QTabWidget::pane { border: 0; }
            QTabBar::tab {
                background: #f6f6ef; 
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid transparent;
                /* Shrink logic */
                min-width: 30px;
                max-width: 200px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #ff6600;
                font-weight: bold;
            }
            QTabBar::tab:hover { background: #e5e5e5; }
        """)
        
        style = self.style()
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self, triggered=lambda: self.tabs.currentWidget().back()))
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Ref", self, triggered=lambda: self.tabs.currentWidget().reload()))
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon), "Home", self, triggered=lambda: self.tabs.currentWidget().setUrl(QUrl(HOME_URL))))
        
        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Search or enter URL")
        self.urlbar.returnPressed.connect(self.navigate)
        self.urlbar.setMinimumWidth(300)
        toolbar.addWidget(self.urlbar)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self.urlbar.setFocus() or self.urlbar.selectAll())
        QShortcut(QKeySequence("Ctrl+T"), self, self.open_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+R"), self, lambda: self.tabs.currentWidget().reload())
        
        self.scroll_j = QShortcut(QKeySequence("J"), self)
        self.scroll_j.activated.connect(lambda: self.run_js("window.scrollBy({top: 100, behavior: 'smooth'});"))
        self.scroll_k = QShortcut(QKeySequence("K"), self)
        self.scroll_k.activated.connect(lambda: self.run_js("window.scrollBy({top: -100, behavior: 'smooth'});"))

    def run_js(self, code):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().page().runJavaScript(code)

    def inject_scripts(self):
        s = QWebEngineScript()
        s.setSourceCode("document.addEventListener('contextmenu', e => window._lastClickPath = e.composedPath(), true);")
        s.setName("ClickTracker")
        s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        self.profile.scripts().insert(s)

    def post_init_setup(self):
        if not self.load_session():
            self.add_new_tab(HOME_URL)
        
        # FIX: Auto-Focus Home Tab after 5 seconds
        QTimer.singleShot(5000, self.focus_home_tab)

    def focus_home_tab(self):
        # 1. Search for existing Home tab
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            url = w.url().toString()
            if "news.ycombinator.com" in url and "item?id=" not in url:
                self.tabs.setCurrentIndex(i)
                return
        
        # 2. If not found, open a fresh one
        self.add_new_tab(HOME_URL)

    def navigate(self):
        view = self.tabs.currentWidget()
        if not view: return
        text = self.urlbar.text().strip()
        if "." not in text and " " in text:
            view.setUrl(QUrl(f"https://www.google.com/search?q={text}"))
        else:
            view.setUrl(QUrl.fromUserInput(text))

    def open_new_tab(self, url=HOME_URL):
        target = url if isinstance(url, str) else HOME_URL
        self.add_new_tab(target)

    def open_dual_tabs(self, article_url, comments_url):
        new_color = self.get_next_group_color()
        
        # 1. Open Article (Immediate + Focus)
        self.add_new_tab(article_url, forced_color=new_color, force_append=True, focus=True)
        
        # 2. Open Comments (Delayed 1.5s + Background)
        QTimer.singleShot(1500, lambda: self.add_new_tab(comments_url, forced_color=new_color, force_append=False, focus=False))

    def add_new_tab(self, url=None, title="New Tab", forced_color=None, restored_color=None, force_append=False, focus=True):
        browser = HNView(self)
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        current_index = self.tabs.currentIndex()
        current_tab = self.tabs.currentWidget()
        
        # --- COLOR LOGIC ---
        if restored_color:
            browser.group_color = restored_color
            insert_mode = "APPEND"
        elif self.tabs.count() == 0:
            browser.group_color = QColor("#000000")
            insert_mode = "APPEND"
        elif forced_color:
            browser.group_color = forced_color
            insert_mode = "APPEND" if force_append else "NEXT"
        elif current_tab and current_tab.group_color.name() == "#ff000000": 
            browser.group_color = self.get_next_group_color()
            insert_mode = "APPEND" 
        elif current_tab and isinstance(current_tab, HNView):
            browser.group_color = current_tab.group_color
            insert_mode = "NEXT"
        else:
            browser.group_color = self.get_next_group_color()
            insert_mode = "APPEND"

        if self.tabs.isVisible() and self.tabs.width() > 100:
             browser.resize(self.tabs.size())
        else:
             browser.resize(1200, 800)
            
        page = HNPage(self.profile, self)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        page.permissionRequested.connect(lambda p: p.grant())
        page.linkHovered.connect(self.status_bar.showMessage)
        browser.setPage(page)
        
        if url: browser.setUrl(QUrl(url))
        
        # --- STUCK LOADING FAILSAFE ---
        def force_title_update():
            if browser.title() in ["", "New Tab"] and browser.url().toString():
                host = browser.url().host()
                if host:
                     update_tab_visuals(browser.url())

        QTimer.singleShot(3000, force_title_update)

        # --- SAFE AUTO-RETRY LOGIC ---
        def handle_load_finished(success):
            self.progress_bar.setVisible(False)
            if not success and browser.retries < 1:
                # If failed (e.g. 429), wait 2s and try ONCE more
                browser.retries += 1
                self.status_bar.showMessage(f"Load failed. Retrying in 2s... ({browser.retries}/1)")
                QTimer.singleShot(2000, browser.reload)

        browser.loadProgress.connect(self.progress_bar.setValue)
        browser.loadStarted.connect(lambda: self.progress_bar.setVisible(True))
        browser.loadFinished.connect(handle_load_finished)

        def update_tab_visuals(qurl):
            if browser == self.tabs.currentWidget():
                self.urlbar.setText(qurl.toString())
            
            host = qurl.host()
            if "ycombinator.com" in host and "item" in qurl.toString():
                browser.content_type = "💬"
            elif "ycombinator.com" in host:
                browser.content_type = "HN" 
            elif not host:
                browser.content_type = "⏳"
            else:
                browser.content_type = "📄"
            
            title = browser.title()
            if not title: title = host if host else "Loading..."
            short_title = title[:20] + ".." if len(title) > 20 else title
            
            idx = self.tabs.indexOf(browser)
            if idx >= 0:
                self.tabs.setTabToolTip(idx, title) 
                
                if browser.content_type == "💬":
                    self.tabs.setTabText(idx, "💬")
                elif browser.content_type == "HN":
                    self.tabs.setTabText(idx, "HN")
                else:
                    self.tabs.setTabText(idx, f"{browser.content_type} {short_title}")
                
                self.tabs.tabBar().setTabTextColor(idx, browser.group_color)

        browser.urlChanged.connect(update_tab_visuals)
        browser.titleChanged.connect(lambda t: update_tab_visuals(browser.url()))

        if insert_mode == "APPEND":
            i = self.tabs.addTab(browser, "New Tab")
        else:
            i = self.tabs.insertTab(current_index + 1, browser, "New Tab")
            
        if focus:
            self.tabs.setCurrentIndex(i)
            
        self.tabs.tabBar().setTabTextColor(i, browser.group_color)
        return page

    # --- CONTEXT MENU ---
    def show_tab_context_menu(self, position):
        index = self.tabs.tabBar().tabAt(position)
        if index == -1: return

        menu = QMenu()
        
        close_action = QAction("Close This Tab", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)
        
        menu.addSeparator()

        close_others = QAction("Close Other Tabs", self)
        close_others.triggered.connect(lambda: self.close_other_tabs(index))
        menu.addAction(close_others)
        
        close_right = QAction("Close Tabs to the Right", self)
        close_right.triggered.connect(lambda: self.close_right_tabs(index))
        menu.addAction(close_right)
        
        close_left = QAction("Close Tabs to the Left", self)
        close_left.triggered.connect(lambda: self.close_left_tabs(index))
        menu.addAction(close_left)
        
        menu.addSeparator()
        
        close_all = QAction("Close All Tabs", self)
        close_all.triggered.connect(self.close_all_tabs)
        menu.addAction(close_all)

        menu.exec(self.tabs.mapToGlobal(position))

    def close_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)
        else: self.close()

    def close_all_tabs(self):
        while self.tabs.count() > 1:
            self.tabs.removeTab(1) 
        if self.tabs.count() == 1 and self.tabs.widget(0).url().toString() != HOME_URL:
             self.tabs.removeTab(0)
             self.add_new_tab(HOME_URL)

    def close_other_tabs(self, keep_index):
        keep_widget = self.tabs.widget(keep_index)
        for i in range(self.tabs.count() - 1, -1, -1):
            if self.tabs.widget(i) != keep_widget:
                self.tabs.removeTab(i)

    def close_right_tabs(self, current_index):
        for i in range(self.tabs.count() - 1, current_index, -1):
            self.tabs.removeTab(i)

    def close_left_tabs(self, current_index):
        for i in range(current_index - 1, -1, -1):
            self.tabs.removeTab(i)

    def handle_tab_change(self, i):
        if i >= 0:
            self.urlbar.setText(self.tabs.widget(i).url().toString())

    def save_session(self):
        tabs = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            tabs.append({
                "url": w.url().toString(),
                "color": w.group_color.name() 
            })
        try:
            with open(get_data_path("session.json"), "w") as f:
                json.dump({"active": self.tabs.currentIndex(), "tabs": tabs}, f)
        except Exception as e:
            logging.error(f"Save Session Error: {e}")

    def load_session(self):
        try:
            with open(get_data_path("session.json"), "r") as f:
                data = json.load(f)
                for t in data.get("tabs", []): 
                    c = t.get("color")
                    color_obj = QColor(c) if c else None
                    self.add_new_tab(t["url"], restored_color=color_obj)
                return True
        except Exception as e:
            logging.error(f"Load Session Error: {e}")
            return False

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = HNBrowser()
    window.showMaximized()
    sys.exit(app.exec())