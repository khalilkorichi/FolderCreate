"""
ui/app_window.py
─────────────────
Executive-Grade Designer Workspace Window:
- Embedded Google Font 'Rubik' dynamically registered via Windows GDI.
- Enforced Right-to-Left (RTL) layout.
- TkinterDnD native Drag-and-Drop capability wrapper:
  Allows dragging and dropping folders/files directly from Windows Explorer
  into Clients Hub, Favorites, or any workspace area.
"""

import os
import customtkinter as ctk

try:
    import tkinterdnd2
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from core.font_loader import load_embedded_fonts
from data.app_store import AppStore
from ui.info_popup import InfoPopup
from ui.dashboard_view import DashboardView
from ui.clients_view import ClientsView
from ui.review_board_view import ReviewBoardView
from ui.favorites_view import FavoritesView
from ui.recents_view import RecentsView
from ui.temp_cleaner_view import TempCleanerView
from ui.template_generator_view import TemplateGeneratorView


VERSION = "0.8"
WINDOW_TITLE = f"Overmind Studios - منصة إدارة الأعمال والتصاميم v{VERSION}"
WINDOW_SIZE = "1130x720"
ICON_PATH = os.path.join(os.getcwd(), "assets", "graphics", "appicon.ico")


if DND_AVAILABLE:
    class BaseCTkWindow(ctk.CTk, tkinterdnd2.TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = tkinterdnd2.TkinterDnD._require(self)
else:
    class BaseCTkWindow(ctk.CTk):
        pass


class AppWindow:
    def __init__(self):
        # 1. Register embedded Rubik font into Windows GDI
        load_embedded_fonts()

        # 2. Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._app = BaseCTkWindow()
        self._app.title(WINDOW_TITLE)
        self._app.geometry(WINDOW_SIZE)
        self._app.minsize(980, 620)
        self._app.option_add("*Font", "Rubik 11")

        if os.path.exists(ICON_PATH):
            try:
                self._app.iconbitmap(ICON_PATH)
            except Exception:
                pass

        # Unified Data Store & Notifications
        self.app_store = AppStore()
        self._info_popup = InfoPopup(self._app)

        # 3. Build Layout: RTL layout (Sidebar packed on RIGHT)
        self._build_sidebar_rtl()
        self._build_content_area()

        # Start at Executive Dashboard
        self._switch_view("dashboard")

    def _build_sidebar_rtl(self):
        self.sidebar_frame = ctk.CTkFrame(self._app, width=235, corner_radius=0)
        self.sidebar_frame.pack(side="right", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Header
        logo_lbl = ctk.CTkLabel(
            self.sidebar_frame,
            text="إدارة مساحة العمل",
            font=("Rubik", 16, "bold")
        )
        logo_lbl.pack(padx=15, pady=(20, 2), anchor="e")

        sub_lbl = ctk.CTkLabel(
            self.sidebar_frame,
            text="Overmind Studios",
            font=("Rubik", 10),
            text_color="gray60"
        )
        sub_lbl.pack(padx=15, pady=(0, 18), anchor="e")

        # Nav Buttons list (RTL-aligned)
        self.nav_buttons = {}

        tabs = [
            ("dashboard", "🏠 الرئيسية (Dashboard)"),
            ("clients", "👥 ملفات العملاء (Clients)"),
            ("reviews", "📋 اعتماد التصاميم (Review)"),
            ("favorites", "⭐ المفضلة (Favorites)"),
            ("recents", "🕒 الأخيرة (Recents)"),
            ("cleaner", "🧹 منظف المؤقتات (Temp)"),
            ("templates", "📁 منشئ القوالب (Templates)"),
        ]

        for key, label in tabs:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                height=38,
                anchor="e",
                font=("Rubik", 11, "bold"),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda k=key: self._switch_view(k)
            )
            btn.pack(fill="x", padx=10, pady=2.5)
            self.nav_buttons[key] = btn

        # Spacer
        ctk.CTkLabel(self.sidebar_frame, text="").pack(expand=True)

        # Theme Selector
        theme_lbl = ctk.CTkLabel(self.sidebar_frame, text="المظهر (Theme):", font=("Rubik", 10), text_color="gray60")
        theme_lbl.pack(padx=15, pady=(5, 0), anchor="e")

        theme_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
            height=26,
            font=("Rubik", 11)
        )
        theme_menu.set("Dark")
        theme_menu.pack(fill="x", padx=12, pady=(2, 10))

        # Version
        ver_lbl = ctk.CTkLabel(
            self.sidebar_frame,
            text=f"v{VERSION} | Overmind Studios",
            font=("Rubik", 9),
            text_color="gray50"
        )
        ver_lbl.pack(pady=(0, 15))

    def _build_content_area(self):
        self.content_container = ctk.CTkFrame(self._app, fg_color="transparent")
        self.content_container.pack(side="left", fill="both", expand=True)

        self._active_key = None
        self._view_factories = {
            "dashboard": lambda: DashboardView(self.content_container, self.app_store, self._switch_view, self._notify),
            "clients": lambda: ClientsView(self.content_container, self.app_store, self._notify),
            "reviews": lambda: ReviewBoardView(self.content_container, self.app_store, self._notify),
            "favorites": lambda: FavoritesView(self.content_container, self.app_store, self._notify),
            "recents": lambda: RecentsView(self.content_container, self.app_store, self._notify),
            "cleaner": lambda: TempCleanerView(self.content_container, self.app_store, self._notify),
            "templates": lambda: TemplateGeneratorView(self.content_container, self._notify),
        }
        self.views = {}

    def _switch_view(self, active_key: str, force_refresh: bool = False):
        if active_key == self._active_key and not force_refresh:
            return

        self._active_key = active_key

        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text_color=["#DCE4EE", "#DCE4EE"])
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        # Hide any inactive view
        for key, view in self.views.items():
            if key != active_key:
                view.pack_forget()

        # Lazily instantiate view on first request
        is_new = False
        if active_key not in self.views:
            factory = self._view_factories.get(active_key)
            if factory:
                self.views[active_key] = factory()
                is_new = True

        target_view = self.views.get(active_key)
        if target_view:
            target_view.pack(fill="both", expand=True)
            if force_refresh:
                if hasattr(target_view, "refresh_dashboard"):
                    target_view.refresh_dashboard()
                elif hasattr(target_view, "refresh_clients"):
                    target_view.refresh_clients()
                elif hasattr(target_view, "refresh_reviews"):
                    target_view.refresh_reviews()
                elif hasattr(target_view, "refresh_favorites"):
                    target_view.refresh_favorites()
                elif hasattr(target_view, "refresh_recents"):
                    target_view.refresh_recents()
                elif hasattr(target_view, "refresh_scan"):
                    target_view.refresh_scan()
            elif not is_new:
                if active_key == "dashboard" and hasattr(target_view, "refresh_dashboard"):
                    target_view.refresh_dashboard()
                elif active_key == "recents" and hasattr(target_view, "refresh_recents"):
                    target_view.refresh_recents()
                elif active_key == "favorites" and hasattr(target_view, "refresh_favorites"):
                    target_view.refresh_favorites()

    def _notify(self, message: str, level: str = "info"):
        self._info_popup.show(message, level=level)

    def _change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode.lower())

    def run(self):
        self._app.mainloop()
