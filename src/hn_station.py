import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QToolBar, QMessageBox, QFileDialog, QMenu, 
                             QSizePolicy, QStatusBar, QWidget, QStyle, QLineEdit, QProgressBar)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, 
                                   QWebEngineSettings, QWebEngineScript)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
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
        
        open_action = QAction("Open Link in New Tab", self)
        open_action.triggered.connect(self.extract_and_open)
        
        copy_action = QAction("Copy Link Address", self)
        copy_action.triggered.connect(self.extract_and_copy)
        
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
        # Default size, but will be overridden by showMaximized()
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
        self.tabs.currentChanged.connect(self.handle_tab_change)
        self.setCentralWidget(self.tabs)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Toolbar
        toolbar = QToolBar("Navigation")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.setStyleSheet("""
            QToolBar { background: #f6f6ef; border-bottom: 2px solid #ff6600; spacing: 8px; padding: 5px; }
            QToolButton { background: transparent; border: none; border-radius: 4px; padding: 4px; color: #333; }
            QToolButton:hover { background: #e5e5e5; }
            QTabWidget::pane { border: 0; }
        """)

        style = self.style()
        
        # Actions
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self, triggered=lambda: self.tabs.currentWidget().back()))
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Refresh", self, triggered=lambda: self.tabs.currentWidget().reload()))
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon), "Home", self, triggered=lambda: self.tabs.currentWidget().setUrl(QUrl(HOME_URL))))
        toolbar.addAction(QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "New Tab", self, triggered=self.open_new_tab))
        
        # URL Bar
        self.urlbar = QLineEdit(self)
        self.urlbar.setPlaceholderText("Search or enter address")
        self.urlbar.returnPressed.connect(self.navigate_to_typed_url)
        self.urlbar.setClearButtonEnabled(True)
        self.urlbar.setMinimumWidth(400)
        toolbar.addWidget(self.urlbar)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self.urlbar.setFocus() or self.urlbar.selectAll())
        QShortcut(QKeySequence("Alt+D"), self, lambda: self.urlbar.setFocus() or self.urlbar.selectAll())
        QShortcut(QKeySequence("Ctrl+R"), self, lambda: self.tabs.currentWidget().reload())
        QShortcut(QKeySequence("Ctrl+T"), self, self.open_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tabs.currentIndex()))

        # Zoom
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addAction(QAction(" A- ", self, triggered=lambda: self.change_zoom(-0.1)))
        toolbar.addAction(QAction(" A+ ", self, triggered=lambda: self.change_zoom(0.1)))

        # --- FIX: DELAYED SESSION LOAD ---
        # Instead of loading immediately, we wait 100ms for the window to actually show up.
        # This ensures the tabs are created at the correct Maximized size.
        QTimer.singleShot(100, self.post_init_setup)

        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_session)
        self.save_timer.start(5000) 

    def post_init_setup(self):
        # This runs after the window is visible
        if not self.load_session():
            self.add_new_tab(HOME_URL)
        # Ensure the first tab URL is synced
        self.handle_tab_change(0)

    def inject_scripts(self):
        s1 = QWebEngineScript()
        s1.setSourceCode("document.addEventListener('contextmenu', e => window._lastClickPath = e.composedPath(), true);")
        s1.setName("ClickTracker")
        s1.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        s1.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        self.profile.scripts().insert(s1)

    def handle_tab_change(self, index):
        if index < 0: return
        view = self.tabs.widget(index)
        if isinstance(view, QWebEngineView):
            self.urlbar.setText(view.url().toString())
            try:
                view.loadProgress.disconnect()
                view.loadStarted.disconnect()
                view.loadFinished.disconnect()
            except: pass
            
            view.loadProgress.connect(self.progress_bar.setValue)
            view.loadStarted.connect(lambda: self.progress_bar.setVisible(True))
            view.loadFinished.connect(lambda: self.progress_bar.setVisible(False))

    def navigate_to_typed_url(self):
        view = self.tabs.currentWidget()
        if not view: return
        text = self.urlbar.text().strip()
        if "." not in text and " " in text:
            view.setUrl(QUrl(f"https://www.google.com/search?q={text}"))
        else:
            view.setUrl(QUrl.fromUserInput(text))

    def change_zoom(self, delta):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setZoomFactor(self.tabs.currentWidget().zoomFactor() + delta)

    def open_new_tab(self):
        self.add_new_tab(HOME_URL)
        self.urlbar.setFocus()
        self.urlbar.selectAll()

    def add_new_tab(self, url=HOME_URL, title="Loading..."):
        browser = HNView(self)
        
        # --- RESIZE LOGIC ---
        # Since we delay loading until the window is visible (thanks to post_init_setup),
        # self.tabs.size() will now return the correct LARGE dimensions (e.g., 1920x1000)
        # instead of the tiny default. This fixes the glitch.
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        if self.tabs.isVisible() and self.tabs.width() > 100:
             browser.resize(self.tabs.size())
        else:
             # Fallback if somehow still hidden
             browser.resize(1200, 800)
            
        page = HNPage(self.profile, self)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        
        page.permissionRequested.connect(lambda p: p.grant())
        page.linkHovered.connect(lambda u: self.status_bar.showMessage(u))

        browser.setPage(page)
        browser.setUrl(QUrl(url))
        browser.urlChanged.connect(lambda u: self.urlbar.setText(u.toString()) if browser == self.tabs.currentWidget() else None)
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(self.tabs.indexOf(browser), t[:20] + "..." if len(t)>20 else t))

        browser.loadProgress.connect(self.progress_bar.setValue)
        browser.loadStarted.connect(lambda: self.progress_bar.setVisible(True))
        browser.loadFinished.connect(lambda: self.progress_bar.setVisible(False))

        i = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(i)
        return page

    def close_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)
        else: self.close()

    def save_session(self):
        tabs = [{"url": self.tabs.widget(i).url().toString()} for i in range(self.tabs.count())]
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