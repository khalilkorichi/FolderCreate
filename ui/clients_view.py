"""
ui/clients_view.py
──────────────────
Visual Client Hub:
- Support for Drag and Drop (سحب وإفلات):
  Users can drag any folder from Windows Explorer and drop it directly onto the client hub.
  The client is automatically registered using the folder's name.
- Search / Filter bar.
- Add Client button.
- Clean RTL card layout with Rubik typography.
"""

import os
import subprocess
import customtkinter as ctk
from PIL import Image

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from data.app_store import AppStore
from core.dnd_helper import parse_dropped_paths
from ui.add_client_dialog import AddClientDialog
from ui.create_month_dialog import CreateMonthDialog
from ui.create_project_dialog import CreateProjectDialog
from ui.confirm_delete_dialog import ConfirmDeleteDialog
from ui.pagination_bar import PaginationBar


class ClientsView(ctk.CTkFrame):
    def __init__(self, parent, app_store: AppStore, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.app_store = app_store
        self.notify = notify_callback
        self._logo_cache = {}
        self._search_timer = None

        self._build_header_rtl()
        self._build_drop_zone_rtl()
        self._build_scrollable_area()
        self.refresh_clients()

    def _build_header_rtl(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 6))

        # Right box: Title & Count in RTL
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="right")

        self.title_lbl = ctk.CTkLabel(
            title_box,
            text="👥 إدارة العملاء ومساحات العمل",
            font=("Rubik", 17, "bold"),
            anchor="e"
        )
        self.title_lbl.pack(anchor="e")

        self.count_lbl = ctk.CTkLabel(
            title_box,
            text="0 عملاء مسجلين",
            font=("Rubik", 11),
            text_color="gray70",
            anchor="e"
        )
        self.count_lbl.pack(anchor="e")

        # Left box: Search & Add client button
        actions_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_box.pack(side="left")

        add_btn = ctk.CTkButton(
            actions_box,
            text="+ إضافة عميل جديد",
            font=("Rubik", 12, "bold"),
            command=self._open_add_client_dialog
        )
        add_btn.pack(side="left", padx=(0, 10))

        self.search_entry = ctk.CTkEntry(
            actions_box,
            placeholder_text="بحث عن عميل بالاسم أو الرمز...",
            width=220,
            font=("Rubik", 11),
            justify="right"
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

    def _on_search_key(self, event=None):
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(160, self.refresh_clients)

    def _build_drop_zone_rtl(self):
        # Interactive Drag and Drop zone
        self.drop_frame = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=("gray85", "gray17"),
            border_width=2,
            border_color=("gray70", "gray30")
        )
        self.drop_frame.pack(fill="x", padx=15, pady=(0, 10))

        drop_text = "📥 اسحب وأفلت مجلدات العملاء السابقة هنا لإدراجها تلقائياً داخل البرنامج"
        self.drop_lbl = ctk.CTkLabel(
            self.drop_frame,
            text=drop_text,
            font=("Rubik", 11, "bold"),
            text_color=("gray30", "gray70")
        )
        self.drop_lbl.pack(pady=10)

        # Register Drag and Drop
        if DND_AVAILABLE:
            try:
                self.drop_frame.drop_target_register(DND_FILES)
                self.drop_frame.dnd_bind("<<Drop>>", self._on_drop_folders)
                self.drop_frame.dnd_bind("<<DropEnter>>", lambda e: self.drop_frame.configure(border_color="#3498DB"))
                self.drop_frame.dnd_bind("<<DropLeave>>", lambda e: self.drop_frame.configure(border_color=("gray70", "gray30")))
            except Exception as e:
                print(f"[clients_view] DnD registration warning: {e}")

    def _on_drop_folders(self, event):
        self.drop_frame.configure(border_color=("gray70", "gray30"))
        paths = parse_dropped_paths(event.data, self.winfo_toplevel())

        added_count = 0
        for p in paths:
            if os.path.isdir(p):
                folder_name = os.path.basename(p)
                words = folder_name.split()
                code_guess = "".join(w[0] for w in words[:3]).upper() if words else "CLT"

                # Check if already registered
                existing = [c for c in self.app_store.get_clients() if os.path.normpath(c.get("root_path", "")) == os.path.normpath(p)]
                if not existing:
                    self.app_store.add_client(
                        name=folder_name,
                        code=code_guess,
                        root_path=p,
                        logo_path=""
                    )
                    added_count += 1

        if added_count > 0:
            self.refresh_clients()
            self.notify(f"تم إدراج {added_count} عميل(اً) بنجاح عبر السحب والإفلات!", level="success")
        elif paths:
            self.notify("المجلدات المسحوبة مسجلة بالفعل أو لم تكن مجلدات صالحة.", level="info")

    def _build_scrollable_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 6))
        self.scroll_frame.grid_columnconfigure((0, 1), weight=1)

        # Pagination bar at bottom
        self.pagination = PaginationBar(
            self,
            total_items=0,
            page_size=10,
            on_page_change=lambda page: self._render_current_page()
        )
        self.pagination.pack(fill="x", padx=15, pady=(0, 10))

        self._cached_filtered_clients = []

    def refresh_clients(self):
        search_query = self.search_entry.get().strip().lower() if hasattr(self, 'search_entry') else ""
        clients = self.app_store.get_clients()

        self._cached_filtered_clients = [
            c for c in clients
            if search_query in c.get("name", "").lower() or search_query in c.get("code", "").lower()
        ]

        total = len(self._cached_filtered_clients)
        self.count_lbl.configure(text=f"{total} عميل متاح في مساحة العمل")
        self.pagination.update_state(total_items=total, reset_to_first=True)
        self._render_current_page()

    def _render_current_page(self):
        # Clear child widgets
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not self._cached_filtered_clients:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="لا يوجد عملاء مسجلين حتى الآن.\nاسحب مجلداً وأفلته في الأعلى، أو اضغط على '+ إضافة عميل جديد'.",
                font=("Rubik", 13),
                text_color="gray60"
            )
            empty_lbl.grid(row=0, column=0, columnspan=2, pady=60)
            return

        page_items = self.pagination.get_slice(self._cached_filtered_clients)
        for idx, client in enumerate(page_items):
            r = idx // 2
            c = 1 - (idx % 2)
            self._render_client_card_rtl(client, r, c)

    def _render_client_card_rtl(self, client: dict, row: int, col: int):
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Top section in RTL (Logo on Right, Info on Left)
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=12, pady=(12, 8))

        logo_widget = self._create_logo_widget(top_frame, client)
        logo_widget.pack(side="right", padx=(12, 0))

        info_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        info_frame.pack(side="right", fill="both", expand=True)

        name_lbl = ctk.CTkLabel(
            info_frame,
            text=client.get("name", "عميل بدون اسم"),
            font=("Rubik", 13, "bold"),
            anchor="e"
        )
        name_lbl.pack(anchor="e")

        code_txt = client.get("code") or "NO-CODE"
        code_lbl = ctk.CTkLabel(
            info_frame,
            text=f"رمز: {code_txt}",
            font=("Rubik", 10),
            text_color="gray60",
            anchor="e"
        )
        code_lbl.pack(anchor="e")

        # Path info
        path_str = client.get("root_path", "")
        short_path = path_str if len(path_str) <= 38 else "..." + path_str[-35:]
        path_lbl = ctk.CTkLabel(
            card,
            text=f"📁 {short_path}",
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        )
        path_lbl.pack(fill="x", padx=12, pady=(0, 10))

        # Quick Actions Bar in RTL sequence
        actions_bar = ctk.CTkFrame(card, fg_color="transparent")
        actions_bar.pack(fill="x", padx=12, pady=(0, 12))

        # 1. Open Folder
        open_btn = ctk.CTkButton(
            actions_bar,
            text="📂 فتح",
            height=28,
            font=("Rubik", 11),
            fg_color=("gray60", "gray30"),
            hover_color=("gray50", "gray25"),
            command=lambda p=path_str: self._open_in_explorer(p)
        )
        open_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # 2. Setup New Month
        month_btn = ctk.CTkButton(
            actions_bar,
            text="📅 شهر",
            height=28,
            font=("Rubik", 11, "bold"),
            command=lambda cl=client: self._open_create_month_dialog(cl)
        )
        month_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # 3. Setup New Post/Project
        post_btn = ctk.CTkButton(
            actions_bar,
            text="🎨 + بوست",
            height=28,
            width=68,
            font=("Rubik", 11, "bold"),
            fg_color="#8E44AD",
            hover_color="#7D3C98",
            command=lambda cl=client: self._open_create_project_dialog(cl)
        )
        post_btn.pack(side="right", padx=(4, 0))

        # 4. Brand Assets
        brand_btn = ctk.CTkButton(
            actions_bar,
            text="الهوية",
            height=28,
            width=48,
            font=("Rubik", 10),
            fg_color=("gray55", "gray25"),
            hover_color=("gray45", "gray20"),
            command=lambda p=path_str: self._open_brand_assets(p)
        )
        brand_btn.pack(side="right", padx=(4, 0))

        # 5. Delete Client (حذف العميل)
        del_btn = ctk.CTkButton(
            actions_bar,
            text="🗑️",
            height=28,
            width=32,
            font=("Rubik", 11),
            fg_color="#C0392B",
            hover_color="#922B21",
            command=lambda cl=client: self._open_delete_client_dialog(cl)
        )
        del_btn.pack(side="right")

    def _create_logo_widget(self, parent, client: dict):
        logo_path = client.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            if logo_path in self._logo_cache:
                return ctk.CTkLabel(parent, image=self._logo_cache[logo_path], text="")
            try:
                pil_img = Image.open(logo_path)
                pil_img.thumbnail((45, 45))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(45, 45))
                self._logo_cache[logo_path] = ctk_img
                return ctk.CTkLabel(parent, image=ctk_img, text="")
            except Exception as e:
                print(f"Error loading logo for {client.get('name')}: {e}")

        initials = (client.get("code") or client.get("name") or "C")[:2].upper()
        mono_frame = ctk.CTkFrame(parent, width=45, height=45, corner_radius=8, fg_color="#1f538d")
        mono_frame.pack_propagate(False)
        ctk.CTkLabel(mono_frame, text=initials, font=("Rubik", 13, "bold"), text_color="white").pack(expand=True)
        return mono_frame

    def _open_in_explorer(self, path: str):
        if not path or not os.path.exists(path):
            self.notify("المسار غير موجود أو تم نقله.", level="error")
            return
        try:
            os.startfile(path)
        except Exception as e:
            subprocess.Popen(["explorer", os.path.normpath(path)])

    def _open_brand_assets(self, root_path: str):
        brand_path = os.path.join(root_path, "_Brand_Assets")
        if not os.path.exists(brand_path):
            os.makedirs(brand_path, exist_ok=True)
        self._open_in_explorer(brand_path)

    def _open_add_client_dialog(self):
        AddClientDialog(self.winfo_toplevel(), on_save_callback=self._handle_client_added)

    def _handle_client_added(self, name: str, code: str, root_path: str, logo_path: str):
        self.app_store.add_client(name, code, root_path, logo_path)
        self.refresh_clients()
        self.notify(f"تم تسجيل العميل '{name}' بنجاح!", level="success")

    def _open_create_month_dialog(self, client: dict):
        CreateMonthDialog(
            self.winfo_toplevel(),
            client_data=client,
            on_success_callback=lambda m_dir, subs: self._handle_month_created(client, m_dir, subs)
        )

    def _handle_month_created(self, client: dict, month_dir: str, created_subfolders: list):
        self.app_store.add_recent("month", f"{client.get('name')} - {os.path.basename(month_dir)}", month_dir)
        self.notify(f"تم إنشاء هيكل الشهر بنجاح:\n{month_dir}", level="success")

    def _open_create_project_dialog(self, client: dict):
        CreateProjectDialog(
            self.winfo_toplevel(),
            client_data=client,
            on_success_callback=lambda p_dir: self._handle_project_created(client, p_dir)
        )

    def _handle_project_created(self, client: dict, project_dir: str):
        self.app_store.add_recent("project", f"{client.get('name')} - {os.path.basename(project_dir)}", project_dir)
        self.notify(f"تم إنشاء مجلد البوست/المشروع بنجاح:\n{project_dir}", level="success")

    def _open_delete_client_dialog(self, client: dict):
        ConfirmDeleteDialog(
            self.winfo_toplevel(),
            client_data=client,
            on_confirm_callback=self._handle_client_deleted
        )

    def _handle_client_deleted(self, client: dict, delete_from_disk: bool, disk_deleted: bool):
        client_id = client.get("id")
        client_name = client.get("name")
        self.app_store.delete_client(client_id)
        self.refresh_clients()

        if delete_from_disk and disk_deleted:
            self.notify(f"تم حذف العميل '{client_name}' ومجلده نهائياً من القرص.", level="success")
        elif delete_from_disk and not disk_deleted:
            self.notify(f"تم حذف العميل '{client_name}' من البرنامج، ولكن تعذر مسح المجلد من القرص (قد يكون مفتوحاً في برنامج آخر).", level="warning")
        else:
            self.notify(f"تم إزالة العميل '{client_name}' من مساحة العمل مع الإبقاء على ملفاته في القرص.", level="info")
