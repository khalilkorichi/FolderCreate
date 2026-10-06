"""
ui/temp_cleaner_view.py
───────────────────────
Temp & Scratchpad Cleaner View:
- Formatted with Rubik typography and RTL orientation.
- Scans `_TEMP` folders across all workspaces.
- 1-Click purge while keeping folders intact for workflow.
"""

import os
import subprocess
import concurrent.futures
import customtkinter as ctk
from data.app_store import AppStore
from core.temp_cleaner import scan_temp_folders, clear_temp_folder
from ui.pagination_bar import PaginationBar


class TempCleanerView(ctk.CTkFrame):
    def __init__(self, parent, app_store: AppStore, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.app_store = app_store
        self.notify = notify_callback
        self.cached_results = []
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="TempCleanerWorker")
        self._is_scanning = False

        self._build_header_rtl()
        self._build_content()
        self.refresh_scan()

    def _build_header_rtl(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        # Right box: Title in RTL
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="right")

        ctk.CTkLabel(
            title_box,
            text="🧹 منظف الملفات المؤقتة",
            font=("Rubik", 17, "bold"),
            anchor="e"
        ).pack(anchor="e")

        self.status_lbl = ctk.CTkLabel(
            title_box,
            text="فحص مجلدات _TEMP التابعة لجميع العملاء لتحرير المساحة",
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        )
        self.status_lbl.pack(anchor="e")

        # Left box: Buttons in RTL
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="left")

        self.clean_all_btn = ctk.CTkButton(
            btn_box,
            text="مسح جميع المؤقتات",
            font=("Rubik", 11, "bold"),
            fg_color="#A93226",
            hover_color="#922B21",
            command=self._clean_all
        )
        self.clean_all_btn.pack(side="left", padx=(0, 8))

        scan_btn = ctk.CTkButton(
            btn_box,
            text="🔄 فحص الآن",
            font=("Rubik", 11),
            width=100,
            command=self.refresh_scan
        )
        scan_btn.pack(side="left")

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

    def refresh_scan(self):
        if self._is_scanning:
            return
        self._is_scanning = True
        self.status_lbl.configure(text="جاري فحص المجلدات المؤقتة للعملاء...")

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        loading_lbl = ctk.CTkLabel(
            self.scroll_frame,
            text="⏳ جاري فحص مجلدات _TEMP وحساب الأحجام بالخلفية...",
            font=("Rubik", 13),
            text_color="gray60"
        )
        loading_lbl.pack(pady=50)

        def _async_worker():
            clients = self.app_store.get_clients()
            all_temps = []
            for c in clients:
                root = c.get("root_path", "")
                if root and os.path.exists(root):
                    scanned = scan_temp_folders(root)
                    for item in scanned:
                        item["client_name"] = c.get("name")
                        all_temps.append(item)
            self.after(0, lambda: self._apply_scan_results(all_temps, len(clients)))

        self._executor.submit(_async_worker)

    def _apply_scan_results(self, all_temps, clients_count):
        self._is_scanning = False
        try:
            if not self.winfo_exists():
                return

            if clients_count == 0:
                for widget in self.scroll_frame.winfo_children():
                    widget.destroy()
                empty_lbl = ctk.CTkLabel(
                    self.scroll_frame,
                    text="لا يوجد عملاء مسجلين لفحص مجلداتهم المؤقتة.\nأضف عميلاً أولاً من تبويب 'العملاء'.",
                    font=("Rubik", 14),
                    text_color="gray60"
                )
                empty_lbl.pack(pady=60)
                self.status_lbl.configure(text="لا يوجد عملاء مسجلين")
                self.pagination.update_state(total_items=0, reset_to_first=True)
                return

            self.cached_results = all_temps
            total_mb = sum(i["size_mb"] for i in all_temps)
            total_files = sum(i["file_count"] for i in all_temps)

            self.status_lbl.configure(
                text=f"تم العثور على {len(all_temps)} مجلد مؤقت | إجمالي {total_files} ملف ({total_mb:.1f} MB)"
            )

            self.pagination.update_state(total_items=len(all_temps), reset_to_first=True)
            self._render_current_page()
        except Exception:
            pass

    def _render_current_page(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.cached_results:
            ctk.CTkLabel(
                self.scroll_frame,
                text="جميع المجلدات المؤقتة نظيفة وفارغة! ✨",
                font=("Rubik", 14),
                text_color="#2ECC71"
            ).pack(pady=60)
            return

        page_items = self.pagination.get_slice(self.cached_results)
        for item in page_items:
            self._render_temp_card_rtl(item)

    def _render_temp_card_rtl(self, item: dict):
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=8)
        card.pack(fill="x", pady=5, padx=5)

        # Right side: Icon + Information (RTL)
        ctk.CTkLabel(card, text="🗑️", font=("Rubik", 18)).pack(side="right", padx=(8, 12), pady=10)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="right", fill="both", expand=True, pady=8)

        ctk.CTkLabel(
            info,
            text=f"{item.get('client_name')} | {item.get('parent_dir')}/_TEMP",
            font=("Rubik", 12, "bold"),
            anchor="e"
        ).pack(anchor="e")

        ctk.CTkLabel(
            info,
            text=item.get("path"),
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(anchor="e")

        # Stats in the center
        stats_txt = f"{item.get('file_count')} ملفات ({item.get('size_mb')} MB)"
        ctk.CTkLabel(
            card,
            text=stats_txt,
            font=("Rubik", 11, "bold"),
            text_color="#F39C12" if item.get('file_count', 0) > 0 else "gray60"
        ).pack(side="left", padx=15)

        # Left side: Action buttons
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="left", padx=10)

        clean_btn = ctk.CTkButton(
            actions,
            text="تفريغ",
            width=65,
            height=28,
            font=("Rubik", 11, "bold"),
            fg_color="#A93226",
            hover_color="#922B21",
            command=lambda p=item.get("path"): self._clean_single(p)
        )
        clean_btn.pack(side="left", padx=(0, 6))

        open_btn = ctk.CTkButton(
            actions,
            text="فتح",
            width=65,
            height=28,
            font=("Rubik", 11),
            command=lambda p=item.get("path"): self._open_dir(p)
        )
        open_btn.pack(side="left")

    def _open_dir(self, path: str):
        if not path or not os.path.exists(path):
            self.notify("المسار غير موجود.", level="error")
            return
        try:
            os.startfile(path)
        except Exception:
            subprocess.Popen(["explorer", os.path.normpath(path)])

    def _clean_single(self, folder_path: str):
        if clear_temp_folder(folder_path, keep_folder=True):
            self.notify(f"تم تفريغ المجلد المؤقت بنجاح:\n{folder_path}", level="success")
            self.refresh_scan()
        else:
            self.notify("فشل تفريغ المجلد.", level="error")

    def _clean_all(self):
        if not self.cached_results:
            return
        cleaned = 0
        for item in self.cached_results:
            if clear_temp_folder(item.get("path"), keep_folder=True):
                cleaned += 1
        self.notify(f"تم تنظيف وتفريغ {cleaned} مجلد(اً) مؤقتاً بنجاح!", level="success")
        self.refresh_scan()
