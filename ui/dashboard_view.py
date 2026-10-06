"""
ui/dashboard_view.py
────────────────────
Executive Designer Dashboard:
- Fully aligned to Rubik typography and Right-To-Left (RTL) standards.
- KPI cards, Fast Actions, and Dual-stream approval/recent lists.
"""

import os
import subprocess
import concurrent.futures
import customtkinter as ctk

from data.app_store import AppStore
from core.review_pipeline import scan_review_files, approve_file
from core.temp_cleaner import scan_temp_folders


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app_store: AppStore, navigate_callback, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.app_store = app_store
        self.navigate = navigate_callback
        self.notify = notify_callback
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="DashWorker")
        self._is_scanning_dashboard = False

        self._build_header_rtl()
        self._build_kpi_cards_rtl()
        self._build_quick_actions_rtl()
        self._build_main_grid_rtl()
        self.refresh_dashboard()

    def _build_header_rtl(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        # RTL Header: Title on Right, Action button on Left
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side="right")

        ctk.CTkLabel(
            right_box,
            text="📊 لوحة التحكم الرئيسية",
            font=("Rubik", 18, "bold"),
            anchor="e"
        ).pack(anchor="e")

        self.subtitle_lbl = ctk.CTkLabel(
            right_box,
            text="نظرة عامة على مشاريع العملاء، تدفق المراجعة والاعتماد، والملفات النشطة",
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        )
        self.subtitle_lbl.pack(anchor="e")

        left_box = ctk.CTkFrame(header, fg_color="transparent")
        left_box.pack(side="left")

        refresh_btn = ctk.CTkButton(
            left_box,
            text="🔄 تحديث البيانات",
            font=("Rubik", 11, "bold"),
            width=120,
            command=lambda: self.refresh_dashboard(force_scan=True)
        )
        refresh_btn.pack(side="left")

    def _build_kpi_cards_rtl(self):
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=15, pady=(5, 10))
        self.kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # RTL order in grid (from column 3 to 0 or right to left):
        # 1. Clients (Rightmost: col 3)
        self.card_clients = self._create_kpi_card(
            self.kpi_container, 3, "العملاء المسجلين", "0", "👥", "#2980B9",
            lambda: self.navigate("clients")
        )
        # 2. In Review (col 2)
        self.card_reviews = self._create_kpi_card(
            self.kpi_container, 2, "بانتظار الاعتماد", "0", "🟡", "#D35400",
            lambda: self.navigate("reviews")
        )
        # 3. Favorites (col 1)
        self.card_favs = self._create_kpi_card(
            self.kpi_container, 1, "الملفات المفضلة", "0", "⭐", "#8E44AD",
            lambda: self.navigate("favorites")
        )
        # 4. Temp files (Leftmost: col 0)
        self.card_temp = self._create_kpi_card(
            self.kpi_container, 0, "ملفات مؤقتة", "0 MB", "🧹", "#27AE60",
            lambda: self.navigate("cleaner")
        )

    def _create_kpi_card(self, parent, col, title, initial_val, icon, accent_color, click_cmd):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=col, padx=5, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Top row: Value on Right, Icon on Left (RTL)
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        val_lbl = ctk.CTkLabel(
            top_row,
            text=initial_val,
            font=("Rubik", 18, "bold"),
            text_color=accent_color,
            anchor="e"
        )
        val_lbl.pack(side="right")

        icon_lbl = ctk.CTkLabel(top_row, text=icon, font=("Rubik", 16))
        icon_lbl.pack(side="left")

        title_lbl = ctk.CTkLabel(
            inner,
            text=title,
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        )
        title_lbl.pack(fill="x", pady=(4, 6))

        btn = ctk.CTkButton(
            inner,
            text="عرض التفاصيل ←",
            height=24,
            font=("Rubik", 10),
            fg_color="transparent",
            text_color=("gray20", "gray80"),
            hover_color=("gray75", "gray25"),
            command=click_cmd
        )
        btn.pack(fill="x")

        return {"val_lbl": val_lbl, "card": card}

    def _build_quick_actions_rtl(self):
        action_bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        action_bar.pack(fill="x", padx=20, pady=(0, 12))

        # Title on Right (RTL)
        ctk.CTkLabel(
            action_bar,
            text="⚡ إجراءات سريعة:",
            font=("Rubik", 12, "bold"),
            anchor="e"
        ).pack(side="right", padx=(12, 15), pady=8)

        # Buttons packed to right in RTL sequence
        b1 = ctk.CTkButton(
            action_bar,
            text="+ عميل جديد",
            height=28,
            font=("Rubik", 11, "bold"),
            command=lambda: self.navigate("clients")
        )
        b1.pack(side="right", padx=4, pady=8)

        b2 = ctk.CTkButton(
            action_bar,
            text="📋 فحص المراجعات",
            height=28,
            font=("Rubik", 11),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray25"),
            command=lambda: self.navigate("reviews")
        )
        b2.pack(side="right", padx=4, pady=8)

        b3 = ctk.CTkButton(
            action_bar,
            text="⭐ فتح المفضلة",
            height=28,
            font=("Rubik", 11),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray25"),
            command=lambda: self.navigate("favorites")
        )
        b3.pack(side="right", padx=4, pady=8)

        b4 = ctk.CTkButton(
            action_bar,
            text="🧹 فحص المؤقتات",
            height=28,
            font=("Rubik", 11),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray25"),
            command=lambda: self.navigate("cleaner")
        )
        b4.pack(side="right", padx=4, pady=8)

        b5 = ctk.CTkButton(
            action_bar,
            text="📁 منشئ القوالب",
            height=28,
            font=("Rubik", 11),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray25"),
            command=lambda: self.navigate("templates")
        )
        b5.pack(side="right", padx=4, pady=8)

    def _build_main_grid_rtl(self):
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        # Column 1 (Right): In-Review designs, Column 0 (Left): Recents
        grid_frame.grid_columnconfigure(0, weight=4)
        grid_frame.grid_columnconfigure(1, weight=6)
        grid_frame.grid_rowconfigure(0, weight=1)

        # ── Column 1 (Right): In-Review Stream ──
        review_box = ctk.CTkFrame(grid_frame, corner_radius=10)
        review_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        review_header = ctk.CTkFrame(review_box, fg_color="transparent")
        review_header.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            review_header,
            text="🟡 تصاميم تنتظر الاعتماد والنقل",
            font=("Rubik", 13, "bold"),
            anchor="e"
        ).pack(side="right")

        ctk.CTkButton(
            review_header,
            text="← لوحة المراجعة",
            height=24,
            font=("Rubik", 10),
            command=lambda: self.navigate("reviews")
        ).pack(side="left")

        self.review_scroll = ctk.CTkScrollableFrame(review_box, fg_color="transparent")
        self.review_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── Column 0 (Left): Recent Activities ──
        recents_box = ctk.CTkFrame(grid_frame, corner_radius=10)
        recents_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        recents_header = ctk.CTkFrame(recents_box, fg_color="transparent")
        recents_header.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            recents_header,
            text="🕒 آخر الأنشطة والمشاريع",
            font=("Rubik", 13, "bold"),
            anchor="e"
        ).pack(side="right")

        ctk.CTkButton(
            recents_header,
            text="← السجل",
            height=24,
            font=("Rubik", 10),
            command=lambda: self.navigate("recents")
        ).pack(side="left")

        self.recents_scroll = ctk.CTkScrollableFrame(recents_box, fg_color="transparent")
        self.recents_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def refresh_dashboard(self, force_scan: bool = False):
        # 1. Instant in-memory stats (0 ms)
        clients = self.app_store.get_clients()
        favs = self.app_store.get_favorites()
        recents = self.app_store.get_recents(limit=8)

        self.card_clients["val_lbl"].configure(text=str(len(clients)))
        self.card_favs["val_lbl"].configure(text=str(len(favs)))

        # Stream of recents (only update if items changed)
        if not hasattr(self, "_cached_recents_ids") or self._cached_recents_ids != [r.get("path") for r in recents]:
            self._cached_recents_ids = [r.get("path") for r in recents]
            for w in self.recents_scroll.winfo_children():
                w.destroy()

            if not recents:
                ctk.CTkLabel(
                    self.recents_scroll,
                    text="لا توجد نشاطات مسجلة بعد.",
                    font=("Rubik", 12),
                    text_color="gray60"
                ).pack(pady=40)
            else:
                for r in recents:
                    self._render_dashboard_recent_card(r)

        # 2. Async disk scans for heavy reviews & temp size
        if self._is_scanning_dashboard:
            return

        # Check if already scanned once and not forcing
        if not force_scan and getattr(self, "_has_initial_scan", False):
            return

        self._is_scanning_dashboard = True

        if not self.review_scroll.winfo_children():
            ctk.CTkLabel(
                self.review_scroll,
                text="⏳ جاري فحص ملفات المراجعة...",
                font=("Rubik", 11),
                text_color="gray60"
            ).pack(pady=35)

        def _async_scan():
            all_reviews = []
            total_temp_mb = 0.0
            for c in clients:
                root = c.get("root_path", "")
                if root and os.path.exists(root):
                    scanned_revs = scan_review_files(root, self.app_store)
                    for item in scanned_revs:
                        item["client_name"] = c.get("name")
                        all_reviews.append(item)

                    scanned_temps = scan_temp_folders(root)
                    for t in scanned_temps:
                        total_temp_mb += t.get("size_mb", 0.0)

            self.after(0, lambda: self._apply_dashboard_scans(all_reviews, total_temp_mb))

        self._executor.submit(_async_scan)

    def _apply_dashboard_scans(self, all_reviews, total_temp_mb):
        self._is_scanning_dashboard = False
        self._has_initial_scan = True
        try:
            if not self.winfo_exists():
                return
            self.card_reviews["val_lbl"].configure(text=str(len(all_reviews)))
            self.card_temp["val_lbl"].configure(text=f"{total_temp_mb:.1f} MB")

            for w in self.review_scroll.winfo_children():
                w.destroy()

            if not all_reviews:
                ctk.CTkLabel(
                    self.review_scroll,
                    text="لا توجد تصاميم قيد المراجعة حالياً ✨\nكل التصاميم معتمدة أو لم تُرفع بعد.",
                    font=("Rubik", 12),
                    text_color="#2ECC71"
                ).pack(pady=40)
            else:
                for item in all_reviews[:6]:
                    self._render_dashboard_review_card(item)
        except Exception:
            pass

    def _render_dashboard_review_card(self, item: dict):
        row = ctk.CTkFrame(self.review_scroll, corner_radius=6, fg_color=("gray85", "gray20"))
        row.pack(fill="x", pady=3, padx=2)

        # Right side: Information labels
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="right", fill="both", expand=True, padx=8, pady=5)

        ctk.CTkLabel(
            info,
            text=item.get("filename"),
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(anchor="e")

        dim_txt = item.get("dimensions_str", "")
        tag_txt = item.get("effective_tag", "")
        meta_txt = f"{item.get('client_name')} • {item.get('month')}"
        if dim_txt and dim_txt != "ملف مشروع":
            meta_txt += f" • {dim_txt}"
        if tag_txt:
            meta_txt += f" • {tag_txt}"

        ctk.CTkLabel(
            info,
            text=meta_txt,
            font=("Rubik", 9),
            text_color="gray70",
            anchor="e"
        ).pack(anchor="e")

        # Left side: Action buttons
        btn_box = ctk.CTkFrame(row, fg_color="transparent")
        btn_box.pack(side="left", padx=6)

        app_b = ctk.CTkButton(
            btn_box,
            text="اعتماد ✅",
            width=70,
            height=25,
            font=("Rubik", 10, "bold"),
            fg_color="#27AE60",
            hover_color="#1E8449",
            command=lambda s=item.get("filepath"), d=item.get("approved_dir"): self._approve_item(s, d)
        )
        app_b.pack(side="left", padx=(0, 4))

        open_b = ctk.CTkButton(
            btn_box,
            text="معاينة",
            width=55,
            height=25,
            font=("Rubik", 10),
            command=lambda p=item.get("filepath"): self._open_path(p)
        )
        open_b.pack(side="left")

    def _render_dashboard_recent_card(self, item: dict):
        row = ctk.CTkFrame(self.recents_scroll, corner_radius=6, fg_color=("gray85", "gray20"))
        row.pack(fill="x", pady=3, padx=2)

        # Info on Right (RTL)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="right", fill="both", expand=True, padx=8, pady=5)

        ctk.CTkLabel(
            info,
            text=f"📁 {item.get('title')}",
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(anchor="e")

        path_txt = item.get("path", "")
        short_p = path_txt if len(path_txt) < 30 else "..." + path_txt[-27:]
        ctk.CTkLabel(
            info,
            text=short_p,
            font=("Rubik", 9),
            text_color="gray70",
            anchor="e"
        ).pack(anchor="e")

        # Open button on Left
        open_b = ctk.CTkButton(
            row,
            text="فتح",
            width=48,
            height=25,
            font=("Rubik", 10),
            command=lambda p=path_txt: self._open_path(p)
        )
        open_b.pack(side="left", padx=6)

    def _approve_item(self, src: str, dest: str):
        if approve_file(src, dest, self.app_store):
            self.notify(f"تم اعتماد ونقل الملف بنجاح إلى:\n{dest}", level="success")
            self.refresh_dashboard()
        else:
            self.notify("حدث خطأ أثناء نقل الملف.", level="error")

    def _open_path(self, path: str):
        if not path or not os.path.exists(path):
            self.notify("المسار غير موجود.", level="error")
            return
        try:
            os.startfile(path)
        except Exception:
            subprocess.Popen(["explorer", os.path.normpath(path)])
