import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QToolBar, QMessageBox, QSizePolicy)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, 
                                   QWebEngineSettings, QWebEngineScript)
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import QUrl, Qt, QTimer

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_user_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_asset_path(filename):
    return os.path.join(get_base_path(), "assets", filename)

def get_data_path(filename):
    return os.path.join(get_user_data_path(), filename)

# --- CUSTOM PAGE ---
class GeminiPage(QWebEnginePage):
    def __init__(self, profile, main_window):
        super().__init__(profile, main_window)
        self.main_window = main_window

    def createWindow(self, _type):
        return self.main_window.add_new_tab()

# --- CUSTOM VIEW ---
class GeminiView(QWebEngineView):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        
        open_action = QAction("Open Link in New Tab", self)
        open_action.triggered.connect(self.extract_and_open)
        
        menu.insertSeparator(menu.actions()[0])
        menu.insertAction(menu.actions()[0], open_action)
        menu.exec(event.globalPos())

    def extract_and_open(self):
        js_code = """
        (function() {
            var path = window._lastClickPath;
            if (!path || path.length === 0) return "";

            for (var i = 0; i < Math.min(path.length, 10); i++) {
                var el = path[i];
                if (el.tagName === 'A' && el.href) return "LINK:" + el.href;
                if (el.getAttribute) {
                    var jslog = el.getAttribute("jslog");
                    if (jslog) {
                        var match = jslog.match(/"c_([^"]+)"/);
                        if (match && match[1]) return "ID:" + match[1];
                    }
                }
            }
            return "";
        })();
        """
        self.page().runJavaScript(js_code, self.handle_extraction)

    def handle_extraction(self, result):
        if not result: return
        url_to_open = ""
        if result.startswith("LINK:"):
            url_to_open = result[5:]
        elif result.startswith("ID:"):
            chat_id = result[3:]
            url_to_open = f"https://gemini.google.com/app/{chat_id}"

        if url_to_open:
            self.main_window.add_new_tab(url_to_open)

# --- MAIN WINDOW ---
class GeminiBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini Station")
        self.resize(1200, 800)
        
        icon_path = get_asset_path("gemini.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Profile
        profile_path = get_data_path("gemini_profile")
        self.profile = QWebEngineProfile("GeminiProfile", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        self.inject_scripts()

        # Tabs Setup
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)             
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)

        # Toolbar
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)
        
        # Actions
        back_btn = QAction(" < ", self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        toolbar.addAction(back_btn)

        refresh_btn = QAction(" ⟳ ", self)
        refresh_btn.setShortcut(QKeySequence("Ctrl+R"))
        refresh_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        toolbar.addAction(refresh_btn)

        new_tab_action = QAction(" + New ", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(lambda: self.add_new_tab())
        toolbar.addAction(new_tab_action)

        dup_action = QAction(" ❐ Duplicate ", self)
        dup_action.triggered.connect(self.duplicate_current_tab)
        toolbar.addAction(dup_action)

        save_btn = QAction(" 💾 Save ", self)
        save_btn.setShortcut(QKeySequence("Ctrl+S"))
        save_btn.triggered.connect(self.manual_save)
        toolbar.addAction(save_btn)

        # Hidden Close Action
        close_act = QAction(self)
        close_act.setShortcut(QKeySequence("Ctrl+W"))
        close_act.triggered.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))
        self.addAction(close_act)

        # SESSION LOAD
        if not self.load_session():
            self.add_new_tab()

        # TIMERS
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_session)
        self.save_timer.start(5000) 

        self.title_timer = QTimer()
        self.title_timer.timeout.connect(self.update_all_titles)
        self.title_timer.start(1000) 

    def inject_scripts(self):
        # 1. Click Tracker
        click_js = """
        (function() {
            document.addEventListener("contextmenu", function(e){
                window._lastClickPath = e.composedPath();
            }, true);
        })();
        """
        script1 = QWebEngineScript()
        script1.setSourceCode(click_js)
        script1.setName("ClickTracker")
        script1.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script1.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        self.profile.scripts().insert(script1)

        # 2. Hide "My Stuff" (SAFE VERSION - Uses textContent)
        # We switched from .innerHTML to .appendChild(document.createTextNode) 
        # to satisfy Google's TrustedHTML security policy.
        css_js = """
        (function() {
            var style = document.createElement('style');
            var css = `
                nav[aria-label*="Recent"], 
                div[data-test-id="recent-chats-list"] { 
                    display: none !important; 
                }
                div:has(> span:contains("My stuff")) {
                    display: none !important;
                }
            `;
            style.appendChild(document.createTextNode(css));
            document.head.appendChild(style);
        })();
        """
        script2 = QWebEngineScript()
        script2.setSourceCode(css_js)
        script2.setName("HideMyStuff")
        script2.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script2.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        self.profile.scripts().insert(script2)

    def add_new_tab(self, url="https://gemini.google.com", title=None):
        browser = GeminiView(self)
        
        # --- FIX FOR JARRING RESIZE ---
        # Resize to full window size IMMEDIATELY, before being added to tabs.
        # This prevents the "small rectangle" animation glitch.
        browser.resize(self.size())
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        page = GeminiPage(self.profile, self)
        
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        page.permissionRequested.connect(lambda p: p.grant())
        
        # --- SCROLL LOGIC ---
        def try_scroll():
            scroll_js = """
            (function() {
                var scroller = document.querySelector('infinite-scroller');
                if (scroller) { 
                    scroller.scrollTop = scroller.scrollHeight;
                    return;
                }
                var containers = document.querySelectorAll('[class*="conversation-container"], [class*="scroll-container"]');
                if (containers.length > 0) {
                    var last = containers[containers.length - 1];
                    last.scrollTop = last.scrollHeight;
                }
                window.scrollTo(0, document.body.scrollHeight);
            })();
            """
            page.runJavaScript(scroll_js)

        page.loadFinished.connect(lambda: QTimer.singleShot(2000, try_scroll))
        page.loadFinished.connect(lambda: QTimer.singleShot(5000, try_scroll))
        page.loadFinished.connect(lambda: QTimer.singleShot(8000, try_scroll))

        browser.setPage(page)
        browser.setUrl(QUrl(url))
        
        initial_title = title if title else "Loading..."
        i = self.tabs.addTab(browser, initial_title)
        self.tabs.setCurrentIndex(i)
        
        return page

    def duplicate_current_tab(self):
        current = self.tabs.currentWidget()
        index = self.tabs.currentIndex()
        if current:
            current_title = self.tabs.tabText(index)
            self.add_new_tab(current.url().toString(), current_title)

    def update_all_titles(self):
        js_code = """
        (function() {
            if (document.hidden) return null;

            try {
                var candidates = [];
                var activeSide = document.querySelector('a[aria-selected="true"], button[aria-selected="true"]');
                if (activeSide) candidates.push(activeSide.innerText);
                var titleBtn = document.querySelector('button[aria-haspopup="menu"]');
                if (titleBtn) candidates.push(titleBtn.innerText);
                var h1 = document.querySelector('h1');
                if (h1) candidates.push(h1.innerText);
                candidates.push(document.title);
                
                var ignore = ["Google Gemini", "Gemini", "Chats", "New chat"];
                for (var i = 0; i < candidates.length; i++) {
                    var t = candidates[i];
                    if (!t) continue;
                    t = t.trim();
                    var isIgnored = ignore.some(bad => t.includes(bad) && t.length < 15);
                    if (t.length > 2 && !isIgnored) return JSON.stringify({title: t, url: window.location.href});
                }
                return JSON.stringify({title: "", url: window.location.href});
            } catch(e) { return ""; }
        })();
        """
        for i in range(self.tabs.count()):
            self.tabs.widget(i).page().runJavaScript(js_code, lambda d, idx=i: self.handle_title(d, idx))

    def handle_title(self, json_str, index):
        if not json_str: return
        try:
            data = json.loads(json_str)
            scraped_title = data.get("title", "").strip()
            url = data.get("url", "")
            
            current_tab_title = self.tabs.tabText(index)
            
            is_scraped_generic = not scraped_title or scraped_title in ["Gemini", "Google Gemini", "Chats"]
            is_current_generic = current_tab_title in ["Loading...", "New Chat"] or current_tab_title.startswith("Chat ") or "Gemini" in current_tab_title

            new_title = current_tab_title 

            if not is_scraped_generic:
                new_title = scraped_title
            elif is_current_generic:
                if "/app/" in url:
                    chat_id = url.split("/")[-1][-4:]
                    new_title = f"Chat {chat_id}"
                else:
                    new_title = "New Chat"
            
            if len(new_title) > 25: new_title = new_title[:25] + "..."
            
            if self.tabs.tabText(index) != new_title:
                self.tabs.setTabText(index, new_title)
        except: pass

    def close_current_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.widget(i).deleteLater()
            self.tabs.removeTab(i)
            self.save_session()
        else:
            self.close()

    def closeEvent(self, event):
        self.save_session()
        event.accept()

    def manual_save(self):
        self.save_session()
        QMessageBox.information(self, "Saved", "Session saved successfully!")

    def save_session(self):
        tab_list = []
        for i in range(self.tabs.count()):
            url = self.tabs.widget(i).url().toString()
            title = self.tabs.tabText(i)
            if "gemini.google.com" in url:
                tab_list.append({"url": url, "title": title})
        
        if not tab_list: return

        session_data = {
            "active_index": self.tabs.currentIndex(),
            "tabs": tab_list
        }

        session_file = get_data_path("session.json")
        try:
            with open(session_file, "w") as f:
                json.dump(session_data, f)
        except: pass

    def load_session(self):
        session_file = get_data_path("session.json")
        if not os.path.exists(session_file):
            return False
        try:
            with open(session_file, "r") as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    tabs = data
                    active_idx = 0
                else:
                    tabs = data.get("tabs", [])
                    active_idx = data.get("active_index", 0)

                if not tabs: return False
                
                print(f" [DEBUG] Loading {len(tabs)} tabs...")
                
                for item in tabs:
                    if isinstance(item, str):
                        self.add_new_tab(item)
                    elif isinstance(item, dict):
                        self.add_new_tab(item.get("url"), item.get("title"))
                
                if active_idx < self.tabs.count():
                    self.tabs.setCurrentIndex(active_idx)
                    
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
    app = QApplication(sys.argv)
    app.setApplicationName("Gemini Station")
    
    window = GeminiBrowser()
    window.showMaximized()
    sys.exit(app.exec())