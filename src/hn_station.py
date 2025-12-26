import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QToolBar, QMessageBox, QFileDialog, QMenu, 
                             QSizePolicy, QStatusBar, QWidget, QStyle, QLineEdit)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, 
                                   QWebEngineSettings, QWebEngineScript)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QColor
from PyQt6.QtCore import QUrl, Qt, QTimer, QSize

# --- CONFIGURATION ---
APP_NAME = "HN App"
HOME_URL = "https://news.ycombinator.com/"
PROFILE_NAME = "HN_Profile"

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

# --- CUSTOM PAGE ---
class HNPage(QWebEnginePage):
    def __init__(self, profile, main_window):
        super().__init__(profile, main_window)
        self.main_window = main_window

    def createWindow(self, _type):
        return self.main_window.add_new_tab()

# --- CUSTOM VIEW ---
class HNView(QWebEngineView):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        
        # Custom Actions
        open_action = QAction("Open Link in New Tab", self)
        open_action.triggered.connect(self.extract_and_open)
        
        copy_action = QAction("Copy Link Address", self)
        copy_action.triggered.connect(self.extract_and_copy)
        
        # Insert at top
        first = menu.actions()[0] if menu.actions() else None
        if first:
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

    def extract_and_open(self):
        self.page().runJavaScript(self.get_hovered_url_js(), self.handle_open)

    def extract_and_copy(self):
        self.page().runJavaScript(self.get_hovered_url_js(), lambda u: QApplication.clipboard().setText(u) if u else None)

    def handle_open(self, url):
        if url: self.main_window.add_new_tab(url)

# --- MAIN WINDOW ---
class HNBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        
        icon_path = get_asset_path("hn.ico") 
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Profile
        profile_path = get_data_path("web_profile")
        self.profile = QWebEngineProfile(PROFILE_NAME, self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        self.inject_scripts()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)             
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(lambda _i: self._sync_urlbar_with_current_tab())
        self.setCentralWidget(self.tabs)

        # Status Bar
        self.setStatusBar(QStatusBar())

        # --- MODERN TOOLBAR SETUP ---
        toolbar = QToolBar("Navigation")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Style the toolbar for a "Modern" look
        self.setStyleSheet("""
            QToolBar {
                background: #f6f6ef; /* HN Beige */
                border-bottom: 2px solid #ff6600; /* HN Orange */
                spacing: 8px;
                padding: 5px;
            }
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
                color: #333;
            }
            QToolButton:hover {
                background: #e5e5e5;
            }
            QTabWidget::pane { border: 0; }
        """)

        # Standard Icons
        style = self.style()
        
        # Back
        btn_back = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self)
        btn_back.triggered.connect(lambda: self.tabs.currentWidget().back())
        toolbar.addAction(btn_back)

        # Refresh
        btn_refresh = QAction(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Refresh", self)
        btn_refresh.setShortcut(QKeySequence("Ctrl+R"))
        btn_refresh.triggered.connect(lambda: self.tabs.currentWidget().reload())
        toolbar.addAction(btn_refresh)

        # Home
        btn_home = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon), "Home", self)
        btn_home.triggered.connect(lambda: self.tabs.currentWidget().setUrl(QUrl(HOME_URL)))
        toolbar.addAction(btn_home)

        # New Tab (Ctrl+T)
        btn_new_tab = QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "New Tab", self)
        btn_new_tab.setShortcut(QKeySequence("Ctrl+T"))
        btn_new_tab.triggered.connect(self.open_new_tab)
        toolbar.addAction(btn_new_tab)
        
        # Dark Mode Toggle (default: light mode)
        self.dark_mode_on = False
        self.btn_dark = QAction("🌙", self)
        self.btn_dark.setToolTip("Enable Dark Mode")
        self.btn_dark.triggered.connect(self.toggle_dark_mode)
        toolbar.addAction(self.btn_dark)

        # URL Bar
        self.urlbar = QLineEdit(self)
        self.urlbar.setPlaceholderText("Type a URL and press Enter")
        self.urlbar.returnPressed.connect(self.navigate_to_typed_url)
        self.urlbar.setClearButtonEnabled(True)
        self.urlbar.setMinimumWidth(450)
        toolbar.addWidget(self.urlbar)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Zoom Controls
        btn_zoom_out = QAction(" A- ", self)
        btn_zoom_out.triggered.connect(lambda: self.change_zoom(-0.1))
        toolbar.addAction(btn_zoom_out)

        btn_zoom_in = QAction(" A+ ", self)
        btn_zoom_in.triggered.connect(lambda: self.change_zoom(0.1))
        toolbar.addAction(btn_zoom_in)

        # Start
        if not self.load_session():
            self.add_new_tab(HOME_URL)

        self._sync_urlbar_with_current_tab()

        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_session)
        self.save_timer.start(5000) 

    def change_zoom(self, delta):
        curr = self.tabs.currentWidget()
        if curr:
            curr.setZoomFactor(curr.zoomFactor() + delta)

    def open_new_tab(self):
        self.add_new_tab(HOME_URL)
        if hasattr(self, "urlbar") and self.urlbar:
            self.urlbar.setFocus()
            self.urlbar.selectAll()

    def _current_view(self) -> QWebEngineView | None:
        w = self.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            return w
        return None

    def _sync_urlbar_with_current_tab(self):
        view = self._current_view()
        if not view or not hasattr(self, "urlbar"):
            return
        try:
            self.urlbar.blockSignals(True)
            self.urlbar.setText(view.url().toString())
        finally:
            self.urlbar.blockSignals(False)

    def navigate_to_typed_url(self):
        view = self._current_view()
        if not view:
            return

        text = self.urlbar.text().strip()
        if not text:
            return

        qurl = QUrl.fromUserInput(text)
        if qurl.isValid():
            view.setUrl(qurl)

    def inject_scripts(self):
        # Click Tracker
        js1 = """
        (function() {
            document.addEventListener("contextmenu", function(e){
                window._lastClickPath = e.composedPath();
            }, true);
        })();
        """
        s1 = QWebEngineScript()
        s1.setSourceCode(js1)
        s1.setName("ClickTracker")
        s1.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        s1.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        self.profile.scripts().insert(s1)

    def _dark_mode_js(self, enabled: bool) -> str:
        if enabled:
            # Keeps the header Orange (#ff6600) but darkens the body nicely
            return """
            (function() {
                var existing = document.getElementById('hn-dark-mode');
                if (existing) return;
                var style = document.createElement('style');
                style.id = 'hn-dark-mode';
                style.textContent = `
                    /* Main Background */
                    body { background-color: #1c1c1c !important; color: #c9d1d9 !important; }
                    table { background-color: transparent !important; }

                    /* The Main Container Table */
                    #hnmain { background-color: #1c1c1c !important; }

                    /* Header (Preserve Orange, but fix text) */
                    #hnmain > tbody > tr:first-child > td { background-color: #ff6600 !important; }

                    /* Links */
                    a:link, a:visited { color: #c9d1d9 !important; }
                    a.storylink { color: #ffffff !important; font-weight: 500; }
                    a:hover { color: #ff6600 !important; text-decoration: underline; }

                    /* Comments & Meta Info */
                    .sitestr { color: #8b949e !important; }
                    .subtext, .subtext a, .comhead, .comhead a { color: #8b949e !important; }

                    /* Input Fields */
                    textarea, input {
                        background-color: #0d1117 !important;
                        color: #c9d1d9 !important;
                        border: 1px solid #30363d;
                        padding: 5px;
                    }

                    /* Vote Arrows (Invert to make them visible on dark) */
                    .votearrow { filter: invert(70%); }

                    /* Code Blocks */
                    pre { background-color: #0d1117; padding: 10px; border-radius: 5px; overflow-x: auto; }
                `;
                document.head.appendChild(style);
            })();
            """
        return """
        (function() {
            var existing = document.getElementById('hn-dark-mode');
            if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
        })();
        """

    def _apply_dark_mode_to_view(self, view: QWebEngineView | None):
        if not view:
            return
        try:
            view.page().runJavaScript(self._dark_mode_js(self.dark_mode_on))
        except Exception:
            pass

    def _apply_dark_mode_to_all_tabs(self):
        for i in range(self.tabs.count()):
            self._apply_dark_mode_to_view(self.tabs.widget(i))

    def toggle_dark_mode(self):
        self.dark_mode_on = not self.dark_mode_on
        if self.dark_mode_on:
            self.btn_dark.setText("☀️")
            self.btn_dark.setToolTip("Disable Dark Mode")
        else:
            self.btn_dark.setText("🌙")
            self.btn_dark.setToolTip("Enable Dark Mode")

        self._apply_dark_mode_to_all_tabs()

    def add_new_tab(self, url=HOME_URL, title="Loading..."):
        browser = HNView(self)
        
        # FIX RESIZE
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if self.tabs.size().isValid():
            browser.resize(self.tabs.size())
            
        page = HNPage(self.profile, self)
        
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        
        page.permissionRequested.connect(lambda p: p.grant())
        page.linkHovered.connect(lambda u: self.statusBar().showMessage(u))

        browser.setPage(page)
        browser.setUrl(QUrl(url))
        browser.urlChanged.connect(lambda u, b=browser: self._sync_urlbar_with_current_tab() if b is self._current_view() else None)
        browser.loadFinished.connect(lambda _ok, b=browser: self._apply_dark_mode_to_view(b))
        browser.titleChanged.connect(lambda t, b=browser: self.set_tab_title(b, t))

        i = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(i)
        return page

    def set_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index != -1:
            if len(title) > 20: title = title[:20] + "..."
            self.tabs.setTabText(index, title)

    def close_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.widget(i).deleteLater()
            self.tabs.removeTab(i)
        else:
            self.close()

    def save_session(self):
        tabs = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            tabs.append({"url": w.url().toString()})
        try:
            with open(get_data_path("session.json"), "w") as f:
                json.dump({"active": self.tabs.currentIndex(), "tabs": tabs}, f)
        except: pass

    def load_session(self):
        try:
            with open(get_data_path("session.json"), "r") as f:
                data = json.load(f)
                for t in data.get("tabs", []): self.add_new_tab(t["url"])
                return True
        except: return False

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = HNBrowser()
    window.showMaximized()
    sys.exit(app.exec())