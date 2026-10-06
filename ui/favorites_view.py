"""
ui/favorites_view.py
────────────────────
Favorites & Pinned Assets View:
- Formatted with Rubik typography and RTL orientation.
- Support for Drag-and-Drop (سحب وإفلات):
  Users can drag any design files (PSD, AI, PDF...) or client folders directly
  from Windows Explorer into the Favorites drop area.
- Pinned PSD/AI files and client folders with 1-click open.
"""

import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from data.app_store import AppStore
from core.dnd_helper import parse_dropped_paths
from ui.confirm_item_delete_dialog import ConfirmItemDeleteDialog
from ui.pagination_bar import PaginationBar


class FavoritesView(ctk.CTkFrame):
    def __init__(self, parent, app_store: AppStore, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.app_store = app_store
        self.notify = notify_callback

        self._build_header_rtl()
        self._build_drop_zone_rtl()
        self._build_content()
        self.refresh_favorites()

    def _build_header_rtl(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 6))

        # Right box: Title in RTL
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="right")

        ctk.CTkLabel(
            title_box,
            text="⭐ الملفات والمجلدات المفضلة",
            font=("Rubik", 17, "bold"),
            anchor="e"
        ).pack(anchor="e")

        ctk.CTkLabel(
            title_box,
            text="وصول سريع فوري لملفات ومجلدات العمل النشطة",
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        ).pack(anchor="e")

        # Left box: Buttons in RTL
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="left")

        add_file_btn = ctk.CTkButton(
            btn_box,
            text="+ إضافة ملف مفضل",
            font=("Rubik", 11, "bold"),
            command=self._add_file_favorite
        )
        add_file_btn.pack(side="left", padx=(0, 8))

        add_folder_btn = ctk.CTkButton(
            btn_box,
            text="+ إضافة مجلد",
            font=("Rubik", 11),
            fg_color=("gray60", "gray30"),
            hover_color=("gray50", "gray25"),
            command=self._add_folder_favorite
        )
        add_folder_btn.pack(side="left")

    def _build_drop_zone_rtl(self):
        self.drop_frame = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=("gray85", "gray17"),
            border_width=2,
            border_color=("gray70", "gray30")
        )
        self.drop_frame.pack(fill="x", padx=15, pady=(0, 10))

        drop_text = "📥 اسحب وأفلت الملفات (PSD / AI / PDF) أو المجلدات هنا لتثبيتها في المفضلة"
        self.drop_lbl = ctk.CTkLabel(
            self.drop_frame,
            text=drop_text,
            font=("Rubik", 11, "bold"),
            text_color=("gray30", "gray70")
        )
        self.drop_lbl.pack(pady=10)

        if DND_AVAILABLE:
            try:
                self.drop_frame.drop_target_register(DND_FILES)
                self.drop_frame.dnd_bind("<<Drop>>", self._on_drop_items)
                self.drop_frame.dnd_bind("<<DropEnter>>", lambda e: self.drop_frame.configure(border_color="#8E44AD"))
                self.drop_frame.dnd_bind("<<DropLeave>>", lambda e: self.drop_frame.configure(border_color=("gray70", "gray30")))
            except Exception as e:
                print(f"[favorites_view] DnD warning: {e}")

    def _on_drop_items(self, event):
        self.drop_frame.configure(border_color=("gray70", "gray30"))
        paths = parse_dropped_paths(event.data, self.winfo_toplevel())

        added_count = 0
        for p in paths:
            item_type = "folder" if os.path.isdir(p) else "file"
            title = os.path.basename(p)
            self.app_store.add_favorite(
                title=title,
                path=p,
                item_type=item_type
            )
            added_count += 1

        if added_count > 0:
            self.refresh_favorites()
            self.notify(f"تمت إضافة {added_count} عنصر(اً) للمفضلة بنجاح عبر السحب والإفلات!", level="success")

    def _build_content(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 6))

        # Pagination Bar
        self.pagination = PaginationBar(
            self,
            total_items=0,
            page_size=12,
            on_page_change=lambda p: self._render_current_page()
        )
        self.pagination.pack(fill="x", padx=15, pady=(0, 10))
        self._cached_favs = []

    def refresh_favorites(self):
        favs = self.app_store.get_favorites()

        # Check if list changed
        if hasattr(self, '_cached_favs') and self._cached_favs == favs:
            return
        self._cached_favs = list(favs)

        self.pagination.update_state(total_items=len(self._cached_favs), reset_to_first=True)
        self._render_current_page()

    def _render_current_page(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self._cached_favs:
            ctk.CTkLabel(
                self.scroll_frame,
                text="لا توجد عناصر مفضلة حتى الآن.\nاسحب وأفلت الملفات في المربع أعلاه لتثبيتها مباشرة.",
                font=("Rubik", 13),
                text_color="gray60"
            ).pack(pady=60)
            return

        page_items = self.pagination.get_slice(self._cached_favs)
        for fav in page_items:
            self._render_fav_item_rtl(fav)

    def _render_fav_item_rtl(self, fav: dict):
        item_frame = ctk.CTkFrame(self.scroll_frame, corner_radius=8)
        item_frame.pack(fill="x", pady=5, padx=5)

        is_folder = fav.get("type") == "folder"
        icon_str = "📁" if is_folder else "📄"

        # Right side: Icon + Information (RTL)
        icon_lbl = ctk.CTkLabel(item_frame, text=icon_str, font=("Rubik", 18))
        icon_lbl.pack(side="right", padx=(8, 12), pady=10)

        details_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        details_frame.pack(side="right", fill="both", expand=True, pady=8)

        title_lbl = ctk.CTkLabel(
            details_frame,
            text=fav.get("title", ""),
            font=("Rubik", 12, "bold"),
            anchor="e"
        )
        title_lbl.pack(anchor="e")

        path_lbl = ctk.CTkLabel(
            details_frame,
            text=fav.get("path", ""),
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        )
        path_lbl.pack(anchor="e")

        # Left side: Action Buttons
        actions_box = ctk.CTkFrame(item_frame, fg_color="transparent")
        actions_box.pack(side="left", padx=10)

        open_btn = ctk.CTkButton(
            actions_box,
            text="فتح الآن",
            width=80,
            height=28,
            font=("Rubik", 11, "bold"),
            command=lambda p=fav.get("path"): self._open_item(p)
        )
        open_btn.pack(side="left", padx=(0, 6))

        del_btn = ctk.CTkButton(
            actions_box,
            text="حذف",
            width=55,
            height=28,
            font=("Rubik", 11),
            fg_color="#A93226",
            hover_color="#922B21",
            command=lambda f=fav: self._open_confirm_delete(f)
        )
        del_btn.pack(side="left")

    def _open_confirm_delete(self, fav: dict):
        ConfirmItemDeleteDialog(
            self.winfo_toplevel(),
            item_data=fav,
            on_confirm_callback=self._handle_item_deleted
        )

    def _handle_item_deleted(self, fav: dict, delete_from_disk: bool, disk_deleted: bool):
        fav_id = fav.get("id")
        title = fav.get("title")
        self.app_store.remove_favorite(fav_id)
        self.refresh_favorites()

        if delete_from_disk and disk_deleted:
            self.notify(f"تم حذف '{title}' نهائياً من القرص والمفضلة.", level="success")
        elif delete_from_disk and not disk_deleted:
            self.notify(f"تمت إزالة '{title}' من المفضلة، لكن تعذر حذفه من القرص (قد يكون قيد الاستخدام).", level="warning")
        else:
            self.notify(f"تمت إزالة '{title}' من قائمة المفضلة بنجاح.", level="info")

    def _add_file_favorite(self):
        file_path = filedialog.askopenfilename(title="اختر ملفاً لإضافته للمفضلة")
        if file_path:
            self.app_store.add_favorite(
                title=os.path.basename(file_path),
                path=file_path,
                item_type="file"
            )
            self.refresh_favorites()
            self.notify("تمت إضافة الملف إلى المفضلة بنجاح!", level="success")

    def _add_folder_favorite(self):
        folder_path = filedialog.askdirectory(title="اختر مجلداً لإضافته للمفضلة")
        if folder_path:
            self.app_store.add_favorite(
                title=os.path.basename(folder_path),
                path=folder_path,
                item_type="folder"
            )
            self.refresh_favorites()
            self.notify("تمت إضافة المجلد إلى المفضلة بنجاح!", level="success")
