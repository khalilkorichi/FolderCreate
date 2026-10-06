"""
ui/review_board_view.py
───────────────────────
Executive Design Review & Approval Hub:
- Grouped by Client: Each client's pending designs are organized in dedicated cards.
- High-Performance Lazy Loading: Background thumbnail worker prevents UI stutter.
- Automatic Dimension & Aspect Ratio Recognition:
    • 9:16 Stories / Reels
    • 4:5 Instagram Posts / Ads
    • 1:1 Square Posts
    • 1.91:1 Link Ads
    • 16:9 Full HD / YouTube
    • Formats & vector badges (PSD, AI, PDF, etc.)
- Customizable Tagging: Quick presets and custom tag editor persisted via AppStore.
- Cut-and-paste approval mechanism transferring files to `03_Approved`.
- Fully compliant with Rubik font & RTL standards.
"""

import os
import subprocess
import concurrent.futures
from typing import Any, Dict, List, Optional
from PIL import Image, ImageOps
import customtkinter as ctk

from data.app_store import AppStore
from core.review_pipeline import scan_review_files, approve_file
from ui.tag_editor_dialog import TagEditorDialog
from ui.pagination_bar import PaginationBar


class ReviewBoardView(ctk.CTkFrame):
    def __init__(self, parent, app_store: AppStore, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.app_store = app_store
        self.notify = notify_callback

        # Memory cache for thumbnails and background thread executor
        self._thumb_cache: Dict[str, Image.Image] = {}
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="ReviewThumbLoader"
        )

        # State
        self.all_reviews: List[Dict[str, Any]] = []
        self.filtered_reviews: List[Dict[str, Any]] = []
        self.client_sections: Dict[str, dict] = {}
        self.is_scanning = False

        self._build_header_rtl()
        self._build_filter_bar_rtl()
        self._build_content_area()
        self.refresh_reviews()

    def _build_header_rtl(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(15, 6))

        # Right box: Title & Subtitle in RTL
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="right")

        ctk.CTkLabel(
            title_box,
            text="📋 اعتماد ومراقبة تصاميم العملاء",
            font=("Rubik", 17, "bold"),
            anchor="e"
        ).pack(anchor="e")

        self.status_lbl = ctk.CTkLabel(
            title_box,
            text="فحص مجلدات (02_In_Review) وتصنيف المقاسات آلياً مع التحميل الكسول السريع",
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        )
        self.status_lbl.pack(anchor="e")

        # Left box: Global Action buttons
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="left")

        self.approve_all_btn = ctk.CTkButton(
            btn_box,
            text="✅ اعتماد ونقل الكل",
            font=("Rubik", 11, "bold"),
            fg_color="#27AE60",
            hover_color="#1E8449",
            command=self._approve_all_global
        )
        self.approve_all_btn.pack(side="left", padx=(0, 8))

        self.refresh_btn = ctk.CTkButton(
            btn_box,
            text="🔄 إعادة الفحص",
            font=("Rubik", 11),
            width=115,
            command=self.refresh_reviews
        )
        self.refresh_btn.pack(side="left")

    def _build_filter_bar_rtl(self):
        """Search and quick filtering bar by client or tag."""
        bar = ctk.CTkFrame(self, fg_color=("gray90", "gray17"), corner_radius=8)
        bar.pack(fill="x", padx=16, pady=(0, 10))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        # Right side: Search entry (RTL)
        ctk.CTkLabel(inner, text="🔍 بحث:", font=("Rubik", 11, "bold")).pack(side="right", padx=(8, 4))

        self.search_entry = ctk.CTkEntry(
            inner,
            placeholder_text="اسم الملف أو التصميم...",
            font=("Rubik", 11),
            width=180,
            justify="right"
        )
        self.search_entry.pack(side="right", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Client dropdown filter
        ctk.CTkLabel(inner, text="العميل:", font=("Rubik", 11)).pack(side="right", padx=(6, 4))
        self.client_filter_menu = ctk.CTkOptionMenu(
            inner,
            values=["جميع العملاء"],
            font=("Rubik", 11),
            width=140,
            command=lambda v: self._apply_filters()
        )
        self.client_filter_menu.pack(side="right", padx=(0, 15))

        # Tag category filter
        ctk.CTkLabel(inner, text="التصنيف:", font=("Rubik", 11)).pack(side="right", padx=(6, 4))
        self.tag_filter_menu = ctk.CTkOptionMenu(
            inner,
            values=[
                "جميع الوسوم",
                "ستوري / ريلز",
                "منشور إنستغرام",
                "منشور مربع",
                "بانر / إعلاني",
                "ملفات مفتوحة (PSD/AI)"
            ],
            font=("Rubik", 11),
            width=150,
            command=lambda v: self._apply_filters()
        )
        self.tag_filter_menu.pack(side="right", padx=(0, 8))

        # Left side: Counter summary badge
        self.counter_badge = ctk.CTkLabel(
            inner,
            text="0 تصميم",
            font=("Rubik", 11, "bold"),
            text_color="#3498DB"
        )
        self.counter_badge.pack(side="left", padx=5)

    def _build_content_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        # Pagination Bar for designs
        self.pagination = PaginationBar(
            self,
            total_items=0,
            page_size=15,
            on_page_change=lambda p: self._render_current_page()
        )
        self.pagination.pack(fill="x", padx=16, pady=(0, 10))

    # ── Scanning & Data Loading ─────────────────────────────────────────────
    def refresh_reviews(self):
        if self.is_scanning:
            return
        self.is_scanning = True
        self.status_lbl.configure(text="جاري فحص مجلدات المراجعة للعملاء...")
        self.refresh_btn.configure(state="disabled")

        # Clear scroll area
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        loading_lbl = ctk.CTkLabel(
            self.scroll_frame,
            text="⏳ جاري فحص وتصنيف التصاميم قيد المراجعة...",
            font=("Rubik", 13),
            text_color="gray60"
        )
        loading_lbl.pack(pady=50)

        # Perform scan in background thread for ultra responsiveness
        self._executor.submit(self._worker_scan_clients)

    def _worker_scan_clients(self):
        clients = self.app_store.get_clients()
        scanned_items = []

        for c in clients:
            root = c.get("root_path", "")
            if root and os.path.exists(root):
                items = scan_review_files(root, self.app_store)
                for item in items:
                    item["client_id"] = c.get("id")
                    item["client_name"] = c.get("name")
                    item["client_code"] = c.get("code")
                    item["client_root"] = root
                    item["client_logo"] = c.get("logo_path", "")
                    scanned_items.append(item)

        # Safely schedule UI update on main thread
        self.after(0, lambda: self._on_scan_completed(scanned_items))

    def _on_scan_completed(self, items: List[Dict[str, Any]]):
        self.is_scanning = False
        self.refresh_btn.configure(state="normal")
        self.all_reviews = items

        # Update client dropdown options
        client_names = sorted(list({it["client_name"] for it in items}))
        options = ["جميع العملاء"] + client_names
        self.client_filter_menu.configure(values=options)
        if self.client_filter_menu.get() not in options:
            self.client_filter_menu.set("جميع العملاء")

        self._apply_filters()

    # ── Filtering & Rendering ───────────────────────────────────────────────
    def _apply_filters(self):
        query = self.search_entry.get().strip().lower()
        selected_client = self.client_filter_menu.get()
        selected_tag = self.tag_filter_menu.get()

        filtered = []
        for it in self.all_reviews:
            # Client filter
            if selected_client != "جميع العملاء" and it.get("client_name") != selected_client:
                continue

            # Tag filter
            if selected_tag != "جميع الوسوم":
                tag_str = it.get("effective_tag", "")
                if selected_tag == "ستوري / ريلز" and "ستوري" not in tag_str and "ريلز" not in tag_str:
                    continue
                elif selected_tag == "منشور إنستغرام" and "إنستغرام" not in tag_str and "4:5" not in tag_str:
                    continue
                elif selected_tag == "منشور مربع" and "مربع" not in tag_str:
                    continue
                elif selected_tag == "بانر / إعلاني" and "بانر" not in tag_str and "إعلاني" not in tag_str:
                    continue
                elif selected_tag == "ملفات مفتوحة (PSD/AI)" and not any(k in tag_str for k in ("PSD", "AI", "فوتوشوب", "إليستريتور")):
                    continue

            # Search text filter
            if query:
                combined = f"{it.get('filename', '')} {it.get('client_name', '')} {it.get('effective_tag', '')}".lower()
                if query not in combined:
                    continue

            filtered.append(it)

        self.filtered_reviews = filtered
        count = len(self.filtered_reviews)
        self.counter_badge.configure(text=f"{count} تصميم ينتظر الاعتماد")
        self.status_lbl.configure(text=f"إجمالي التصاميم قيد المراجعة: {len(self.all_reviews)} | المعروض حالياً: {count}")
        self.pagination.update_state(total_items=count, reset_to_first=True)
        self._render_current_page()

    def _render_current_page(self):
        # Clear existing items
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.filtered_reviews:
            empty_box = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            empty_box.pack(pady=70)

            ctk.CTkLabel(
                empty_box,
                text="🎉",
                font=("Rubik", 44)
            ).pack(pady=(0, 10))

            if not self.all_reviews:
                msg = "جميع تصاميم العملاء معتمدة ومكتملة!\nلا توجد تصاميم قيد المراجعة داخل مجلدات (02_In_Review) حالياً."
            else:
                msg = "لا توجد نتائج تطابق خيارات التصفية أو البحث الحالية."

            ctk.CTkLabel(
                empty_box,
                text=msg,
                font=("Rubik", 14),
                text_color="#2ECC71" if not self.all_reviews else "gray60",
                justify="center"
            ).pack()
            return

        # Get the slice for the current page
        page_items = self.pagination.get_slice(self.filtered_reviews)

        # Group current page items by client
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for it in page_items:
            c_name = it.get("client_name", "عميل غير محدد")
            grouped.setdefault(c_name, []).append(it)

        # Render client sections for current page
        for client_name, client_items in grouped.items():
            self._render_client_section(client_name, client_items)

    def _render_client_section(self, client_name: str, items: List[Dict[str, Any]]):
        """Creates a dedicated accordion section for each client with pending designs."""
        sample = items[0]
        client_code = sample.get("client_code", "")
        client_root = sample.get("client_root", "")

        section = ctk.CTkFrame(self.scroll_frame, corner_radius=10, fg_color=("gray85", "gray18"))
        section.pack(fill="x", pady=8, padx=4)

        # ── Section Header (RTL) ──
        header_bar = ctk.CTkFrame(section, corner_radius=8, fg_color=("gray80", "gray22"))
        header_bar.pack(fill="x", padx=6, pady=6)

        # Right side: Client avatar + Name + Count badge
        right_box = ctk.CTkFrame(header_bar, fg_color="transparent")
        right_box.pack(side="right", padx=10, pady=8)

        # Client monogram badge
        mono_lbl = ctk.CTkLabel(
            right_box,
            text=client_code or client_name[:1],
            width=36,
            height=36,
            corner_radius=18,
            font=("Rubik", 13, "bold"),
            fg_color="#2980B9",
            text_color="white"
        )
        mono_lbl.pack(side="right", padx=(8, 0))

        info_box = ctk.CTkFrame(right_box, fg_color="transparent")
        info_box.pack(side="right")

        name_row = ctk.CTkFrame(info_box, fg_color="transparent")
        name_row.pack(anchor="e")

        ctk.CTkLabel(
            name_row,
            text=client_name,
            font=("Rubik", 14, "bold"),
            anchor="e"
        ).pack(side="right")

        # Count badge
        ctk.CTkLabel(
            name_row,
            text=f" ({len(items)} تصميم)",
            font=("Rubik", 11),
            text_color="#F39C12",
            anchor="e"
        ).pack(side="right", padx=6)

        sub_info = f"المسار: {client_root}" if len(client_root) < 55 else f"المسار: ...{client_root[-50:]}"
        ctk.CTkLabel(
            info_box,
            text=sub_info,
            font=("Rubik", 9),
            text_color="gray60",
            anchor="e"
        ).pack(anchor="e")

        # Left side: Client actions (Approve All for Client, Open folder, Toggle)
        left_box = ctk.CTkFrame(header_bar, fg_color="transparent")
        left_box.pack(side="left", padx=10, pady=8)

        # Content container inside section (Hidden by default)
        items_container = ctk.CTkFrame(section, fg_color="transparent")

        # Toggle collapse/expand state (Closed by default)
        is_collapsed = [True]
        rendered_once = [False]

        def toggle_collapse():
            if is_collapsed[0]:
                # Lazily render designs on first open
                if not rendered_once[0]:
                    for itm in items:
                        self._render_design_card_rtl(items_container, itm)
                    rendered_once[0] = True

                items_container.pack(fill="x", padx=8, pady=(0, 8))
                toggle_btn.configure(text="▲ إخفاء")
                is_collapsed[0] = False
            else:
                items_container.pack_forget()
                toggle_btn.configure(text="▼ عرض")
                is_collapsed[0] = True

        toggle_btn = ctk.CTkButton(
            left_box,
            text="▼ عرض",
            width=65,
            height=28,
            font=("Rubik", 10),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray25"),
            command=toggle_collapse
        )
        toggle_btn.pack(side="left", padx=(0, 6))

        # Open client folder button
        open_folder_btn = ctk.CTkButton(
            left_box,
            text="📂 مجلد العميل",
            width=95,
            height=28,
            font=("Rubik", 10),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray25"),
            command=lambda r=client_root: self._open_path(r)
        )
        open_folder_btn.pack(side="left", padx=(0, 6))

        # Approve all designs for this client button
        approve_client_btn = ctk.CTkButton(
            left_box,
            text=f"اعتماد تصاميم العميل ({len(items)}) ✅",
            height=28,
            font=("Rubik", 10, "bold"),
            fg_color="#27AE60",
            hover_color="#1E8449",
            command=lambda c_items=items, c_n=client_name: self._approve_client_designs(c_n, c_items)
        )
        approve_client_btn.pack(side="left")

    def _render_design_card_rtl(self, parent, item: Dict[str, Any]):
        """Renders an individual design card with lazy loaded thumbnail and dimension badges."""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray92", "gray23"))
        card.pack(fill="x", pady=4, padx=2)

        # ── Right Side: Thumbnail + File Info + Badges (RTL) ──
        right_container = ctk.CTkFrame(card, fg_color="transparent")
        right_container.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        # Thumbnail Box (72x72)
        thumb_box = ctk.CTkFrame(right_container, width=72, height=72, corner_radius=6, fg_color=("gray80", "gray18"))
        thumb_box.pack(side="right", padx=(8, 0))
        thumb_box.pack_propagate(False)

        # Placeholder label inside thumb box
        file_path = item.get("filepath", "")
        is_img = item.get("is_image", False)

        if is_img:
            thumb_lbl = ctk.CTkLabel(thumb_box, text="⏳", font=("Rubik", 16))
            thumb_lbl.pack(fill="both", expand=True)

            # Lazy load thumbnail asynchronously
            self._lazy_load_thumbnail(file_path, thumb_lbl)
        else:
            # Styled badge icon for PSD, AI, PDF, etc.
            _, ext = os.path.splitext(file_path)
            clean_ext = ext.replace(".", "").upper()[:4] or "FILE"
            badge_color = item.get("tag_color", "#7F8C8D")

            icon_frame = ctk.CTkFrame(thumb_box, fg_color=badge_color, corner_radius=4)
            icon_frame.pack(fill="both", expand=True, padx=8, pady=8)
            ctk.CTkLabel(
                icon_frame,
                text=clean_ext,
                font=("Rubik", 11, "bold"),
                text_color="white"
            ).pack(expand=True)

        # Information column
        info_col = ctk.CTkFrame(right_container, fg_color="transparent")
        info_col.pack(side="right", fill="both", expand=True, padx=(0, 8))

        # Row 1: File name and size
        name_row = ctk.CTkFrame(info_col, fg_color="transparent")
        name_row.pack(fill="x", anchor="e")

        disp_filename = item.get("filename", "")
        if len(disp_filename) > 36:
            disp_filename = disp_filename[:33] + "..."

        ctk.CTkLabel(
            name_row,
            text=disp_filename,
            font=("Rubik", 12, "bold"),
            anchor="e"
        ).pack(side="right")

        ctk.CTkLabel(
            name_row,
            text=f"  ({item.get('size_display', '')})",
            font=("Rubik", 10),
            text_color="gray60",
            anchor="e"
        ).pack(side="right")

        # Row 2: Location (Year • Month)
        loc_str = f"📅 {item.get('year')} • {item.get('month')}"
        ctk.CTkLabel(
            info_col,
            text=loc_str,
            font=("Rubik", 9),
            text_color="gray60",
            anchor="e"
        ).pack(fill="x", anchor="e", pady=(2, 4))

        # Row 3: Dimensions badge & Tag badge
        badges_row = ctk.CTkFrame(info_col, fg_color="transparent")
        badges_row.pack(fill="x", anchor="e")

        # 1. Dimensions badge
        dim_str = item.get("dimensions_str", "")
        if dim_str and dim_str != "ملف مشروع":
            dim_lbl = ctk.CTkLabel(
                badges_row,
                text=f"📏 {dim_str}",
                font=("Rubik", 9, "bold"),
                fg_color=("gray80", "gray30"),
                corner_radius=4,
                padx=6,
                pady=1
            )
            dim_lbl.pack(side="right", padx=(4, 0))

        # 2. Tag badge (with distinct color)
        tag_color = item.get("tag_color", "#2980B9")
        tag_lbl = ctk.CTkLabel(
            badges_row,
            text=item.get("effective_tag", "ملف تصميم"),
            font=("Rubik", 9, "bold"),
            fg_color=tag_color,
            text_color="white",
            corner_radius=4,
            padx=7,
            pady=1
        )
        tag_lbl.pack(side="right", padx=(4, 0))

        # If user customized this tag, show an indicator
        if item.get("is_custom_tagged"):
            ctk.CTkLabel(
                badges_row,
                text="⭐ مخصص",
                font=("Rubik", 8),
                text_color="#F39C12"
            ).pack(side="right", padx=(2, 0))

        # ── Left Side: Action Buttons ──
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="left", padx=10, pady=8)

        # 1. Approve & Transfer button
        approve_btn = ctk.CTkButton(
            actions,
            text="اعتماد ونقل ✅",
            width=100,
            height=28,
            font=("Rubik", 10, "bold"),
            fg_color="#27AE60",
            hover_color="#1E8449",
            command=lambda it=item: self._approve_single_design(it)
        )
        approve_btn.pack(side="left", padx=(0, 6))

        # 2. Edit Tag button
        edit_tag_btn = ctk.CTkButton(
            actions,
            text="🏷️ تعديل الوسم",
            width=90,
            height=28,
            font=("Rubik", 10),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray25"),
            command=lambda it=item: self._open_tag_editor(it)
        )
        edit_tag_btn.pack(side="left", padx=(0, 6))

        # 3. Preview button
        preview_btn = ctk.CTkButton(
            actions,
            text="👁️ معاينة",
            width=65,
            height=28,
            font=("Rubik", 10),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray25"),
            command=lambda p=file_path: self._open_path(p)
        )
        preview_btn.pack(side="left")

    # ── Lazy Thumbnail Generation ───────────────────────────────────────────
    def _lazy_load_thumbnail(self, filepath: str, label_widget: ctk.CTkLabel):
        """Asynchronously loads or fetches thumbnail from memory cache without UI freeze."""
        if filepath in self._thumb_cache:
            # Cached in memory
            pil_thumb = self._thumb_cache[filepath]
            self._apply_thumbnail(label_widget, pil_thumb)
            return

        def _loader():
            try:
                with Image.open(filepath) as img:
                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception:
                        pass
                    # Crisp 144x144 for high-DPI scaling down to 72x72
                    thumb = ImageOps.fit(img, (144, 144), method=Image.Resampling.LANCZOS)
                    pil_thumb = thumb.convert("RGBA")
                    self._thumb_cache[filepath] = pil_thumb
                    self.after(0, lambda: self._apply_thumbnail(label_widget, pil_thumb))
            except Exception:
                # If reading thumbnail fails, display fallback icon
                self.after(0, lambda: self._apply_thumbnail_error(label_widget))

        self._executor.submit(_loader)

    def _apply_thumbnail(self, label_widget: ctk.CTkLabel, pil_thumb: Image.Image):
        try:
            if label_widget.winfo_exists():
                ctk_img = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=(72, 72))
                label_widget.configure(image=ctk_img, text="")
        except Exception:
            pass

    def _apply_thumbnail_error(self, label_widget: ctk.CTkLabel):
        try:
            if label_widget.winfo_exists():
                label_widget.configure(text="🖼️", font=("Rubik", 16))
        except Exception:
            pass

    # ── Tag Editing ─────────────────────────────────────────────────────────
    def _open_tag_editor(self, item: Dict[str, Any]):
        filepath = item.get("filepath", "")

        def _on_save(new_tag: str):
            if new_tag:
                self.app_store.set_design_tag(filepath, new_tag)
                self.notify(f"تم حفظ وسم التصميم: {new_tag}", level="success")
            else:
                self.app_store.remove_design_tag(filepath)
                self.notify("تمت استعادة الوسم التلقائي للتصميم.", level="info")

            # Update cache without scanning whole disk
            custom_tag = self.app_store.get_design_tag(filepath)
            for it in self.all_reviews:
                if it.get("filepath") == filepath:
                    if custom_tag:
                        it["effective_tag"] = f"🏷️ {custom_tag}"
                        it["is_custom_tagged"] = True
                        it["tag_color"] = "#F39C12"
                    else:
                        it["effective_tag"] = it.get("auto_tag")
                        it["is_custom_tagged"] = False
                        it["tag_color"] = item.get("auto_tag_color", "#2980B9")
            self._apply_filters()

        TagEditorDialog(
            parent=self.winfo_toplevel(),
            filename=item.get("filename", ""),
            dimensions_str=item.get("dimensions_str", ""),
            current_tag=item.get("effective_tag", ""),
            on_save=_on_save
        )

    # ── Approval Actions ────────────────────────────────────────────────────
    def _approve_single_design(self, item: Dict[str, Any]):
        src = item.get("filepath")
        dest = item.get("approved_dir")
        if approve_file(src, dest, self.app_store):
            self.notify(f"تم اعتماد ونقل التصميم بنجاح إلى:\n{dest}", level="success")
            # Remove from local lists
            self.all_reviews = [it for it in self.all_reviews if it.get("filepath") != src]
            self._apply_filters()
        else:
            self.notify("حدث خطأ أثناء نقل الملف.", level="error")

    def _approve_client_designs(self, client_name: str, items: List[Dict[str, Any]]):
        approved_count = 0
        for it in items:
            src = it.get("filepath")
            dest = it.get("approved_dir")
            if approve_file(src, dest, self.app_store):
                approved_count += 1

        self.notify(f"تم اعتماد ونقل {approved_count} تصميم(اً) للعميل [{client_name}] بنجاح!", level="success")
        approved_paths = {it.get("filepath") for it in items}
        self.all_reviews = [it for it in self.all_reviews if it.get("filepath") not in approved_paths]
        self._apply_filters()

    def _approve_all_global(self):
        if not self.all_reviews:
            self.notify("لا توجد تصاميم قيد المراجعة لنقلها.", level="info")
            return

        approved_count = 0
        for it in list(self.all_reviews):
            src = it.get("filepath")
            dest = it.get("approved_dir")
            if approve_file(src, dest, self.app_store):
                approved_count += 1

        self.notify(f"تم اعتماد ونقل جميع التصاميم ({approved_count} تصميم) إلى مجلدات المعتمدة بنجاح! 🎉", level="success")
        self.refresh_reviews()

    def _open_path(self, path: str):
        if not path or not os.path.exists(path):
            self.notify("المسار غير موجود أو تم نقله.", level="error")
            return
        try:
            os.startfile(path)
        except Exception:
            subprocess.Popen(["explorer", os.path.normpath(path)])
