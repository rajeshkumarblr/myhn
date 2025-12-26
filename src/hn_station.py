import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QToolBar, QMessageBox, QFileDialog, QMenu, 
                             QSizePolicy, QStatusBar, QWidget)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, 
                                   QWebEngineSettings, QWebEngineScript)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont
from PyQt6.QtCore import QUrl, Qt, QTimer

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
        self.setCentralWidget(self.tabs)

        # Status Bar (New!)
        self.setStatusBar(QStatusBar())

        # Toolbar
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)
        
        # Nav Buttons
        for text, func in [(" < ", lambda: self.tabs.currentWidget().back()),
                           (" ⟳ ", lambda: self.tabs.currentWidget().reload()),
                           (" Home ", lambda: self.tabs.currentWidget().setUrl(QUrl(HOME_URL)))]:
            a = QAction(text, self)
            a.triggered.connect(func)
            toolbar.addAction(a)

        # Dark Mode
        self.dark_mode_on = True
        dark_btn = QAction(" 🌙 ", self)
        dark_btn.triggered.connect(self.toggle_dark_mode)
        toolbar.addAction(dark_btn)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Zoom Controls
        zoom_out = QAction(" - ", self)
        zoom_out.triggered.connect(lambda: self.change_zoom(-0.1))
        toolbar.addAction(zoom_out)

        zoom_in = QAction(" + ", self)
        zoom_in.triggered.connect(lambda: self.change_zoom(0.1))
        toolbar.addAction(zoom_in)

        # Start
        if not self.load_session():
            self.add_new_tab(HOME_URL)

        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_session)
        self.save_timer.start(5000) 

    def change_zoom(self, delta):
        curr = self.tabs.currentWidget()
        if curr:
            curr.setZoomFactor(curr.zoomFactor() + delta)

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
        
        self.inject_dark_mode_script()

    def inject_dark_mode_script(self):
        css = """
        (function() {
            if (document.getElementById('hn-dark-mode')) return;
            var style = document.createElement('style');
            style.id = 'hn-dark-mode';
            style.textContent = `
                body { background-color: #1e1e1e !important; color: #d4d4d4 !important; }
                table, tr, td { background-color: #1e1e1e !important; }
                a:link, a:visited { color: #61afef !important; text-decoration: none; }
                a:hover { text-decoration: underline; color: #98c379 !important; }
                .sitestr { color: #abb2bf !important; }
                .hnname a { color: #ff6600 !important; }
                textarea, input { background-color: #2c2c2c !important; color: white !important; border: 1px solid #444; }
                .c00, .c00 a:link { color: #d4d4d4 !important; }
                .votearrow { filter: invert(100%); }
            `;
            document.head.appendChild(style);
        })();
        """
        s = QWebEngineScript()
        s.setSourceCode(css)
        s.setName("DarkTheme")
        s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        self.profile.scripts().insert(s)

    def toggle_dark_mode(self):
        self.dark_mode_on = not self.dark_mode_on
        if not self.dark_mode_on:
            dummy = QWebEngineScript()
            dummy.setName("DarkTheme")
            dummy.setSourceCode("/* Disabled */")
            self.profile.scripts().insert(dummy)
        else:
            self.inject_dark_mode_script()
        self.tabs.currentWidget().reload()

    def add_new_tab(self, url=HOME_URL, title="Loading..."):
        browser = HNView(self)
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if self.tabs.size().isValid():
            browser.resize(self.tabs.size())
            
        page = HNPage(self.profile, self)
        
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        
        page.permissionRequested.connect(lambda p: p.grant())
        
        # Connect Status Bar
        page.linkHovered.connect(lambda u: self.statusBar().showMessage(u))

        browser.setPage(page)
        browser.setUrl(QUrl(url))
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

