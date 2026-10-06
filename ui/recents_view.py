"""
ui/recents_view.py
──────────────────
Recent Activity View:
- Formatted with Rubik typography and RTL orientation.
- Timeline of recently accessed clients, files, and generated months.
"""

import os
import subprocess
from datetime import datetime
import customtkinter as ctk
from data.app_store import AppStore
from ui.pagination_bar import PaginationBar


class RecentsView(ctk.CTkFrame):
    def __init__(self, parent, app_store: AppStore, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.app_store = app_store
        self.notify = notify_callback

        self._build_header_rtl()
        self._build_content()
        self.refresh_recents()

    def _build_header_rtl(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        # Right box: Title in RTL
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="right")

        ctk.CTkLabel(
            title_box,
            text="🕒 العناصر والمجلدات المستخدمة مؤخراً",
            font=("Rubik", 17, "bold"),
            anchor="e"
        ).pack(anchor="e")

        ctk.CTkLabel(
            title_box,
            text="سجل المجلدات والملفات التي تم العمل عليها مؤخراً",
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        ).pack(anchor="e")

        # Left box: Refresh button
        refresh_btn = ctk.CTkButton(
            header,
            text="تحديث القائمة",
            font=("Rubik", 11),
            width=110,
            command=self.refresh_recents
        )
        refresh_btn.pack(side="left")

    def _build_content(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 6))

        # Pagination Bar
        self.pagination = PaginationBar(
            self,
            total_items=0,
            page_size=15,
            on_page_change=lambda p: self._render_current_page()
        )
        self.pagination.pack(fill="x", padx=15, pady=(0, 10))
        self._cached_recents = []

    def refresh_recents(self):
        recents = self.app_store.get_recents(limit=100)

        # Check if list changed
        if hasattr(self, '_cached_recents') and self._cached_recents == recents:
            return
        self._cached_recents = list(recents)

        self.pagination.update_state(total_items=len(self._cached_recents), reset_to_first=True)
        self._render_current_page()

    def _render_current_page(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self._cached_recents:
            ctk.CTkLabel(
                self.scroll_frame,
                text="لا توجد أنشطة مسجلة مؤخراً حتى الآن.",
                font=("Rubik", 14),
                text_color="gray60"
            ).pack(pady=60)
            return

        page_items = self.pagination.get_slice(self._cached_recents)
        for item in page_items:
            self._render_recent_item_rtl(item)

    def _render_recent_item_rtl(self, item: dict):
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=8)
        card.pack(fill="x", pady=4, padx=5)

        icon_str = "📂" if item.get("type") in ["folder", "client", "month", "project"] else "📄"

        # Right side: Icon + Title/Path (RTL)
        ctk.CTkLabel(card, text=icon_str, font=("Rubik", 17)).pack(side="right", padx=(8, 12), pady=8)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="right", fill="both", expand=True, pady=6)

        ctk.CTkLabel(
            info,
            text=item.get("title", "عنصر بدون اسم"),
            font=("Rubik", 12, "bold"),
            anchor="e"
        ).pack(anchor="e")

        path_txt = item.get("path", "")
        ctk.CTkLabel(
            info,
            text=path_txt,
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(anchor="e")

        # Timestamp on the left
        time_str = item.get("timestamp", "")
        formatted_time = ""
        if time_str:
            try:
                dt = datetime.fromisoformat(time_str)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                formatted_time = time_str[:16]

        ctk.CTkLabel(
            card,
            text=formatted_time,
            font=("Rubik", 10),
            text_color="gray60"
        ).pack(side="left", padx=(10, 5))

        open_btn = ctk.CTkButton(
            card,
            text="فتح",
            width=65,
            height=28,
            font=("Rubik", 11),
            command=lambda p=path_txt: self._open_path(p)
        )
        open_btn.pack(side="left", padx=10)

    def _open_path(self, path: str):
        if not path or not os.path.exists(path):
            self.notify("المسار لم يعد موجوداً على القرص.", level="error")
            return
        try:
            os.startfile(path)
        except Exception:
            subprocess.Popen(["explorer", os.path.normpath(path)])
