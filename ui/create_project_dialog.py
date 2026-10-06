"""
ui/create_project_dialog.py
───────────────────────────
Modal dialog to create an individual project/post folder inside a chosen client's month:
Formatted with Rubik font and RTL alignment.
"""

import os
from datetime import datetime
import customtkinter as ctk
from core.client_manager import get_existing_client_years, get_existing_months_for_year


PROJECT_SUBFOLDERS = [
    "00_Resources",
    "01_Sources_PSD",
    "02_In_Review",
    "03_Approved",
    "_TEMP"
]


class CreateProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent, client_data, on_success_callback):
        super().__init__(parent)
        self.title("إنشاء مجلد مشروع أو بوست جديد")
        self.geometry("490x440")
        self.resizable(False, False)

        self.client_data = client_data
        self.on_success_callback = on_success_callback

        self.attributes("-topmost", True)
        self.grab_set()

        self._build_ui_rtl()
        self._center(parent)

    def _build_ui_rtl(self):
        pad_x = 22
        root_path = self.client_data.get("root_path", "")

        # Title (RTL)
        ctk.CTkLabel(
            self,
            text=f"إنشاء مجلد بوست/تصميم لـ: {self.client_data.get('name')}",
            font=("Rubik", 14, "bold"),
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(15, 8))

        # Project Name input (RTL)
        ctk.CTkLabel(self, text="اسم المشروع أو البوست الإعلاني:", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(5, 0))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="مثال: Post_Discount_Summer أو Banner_Promo", font=("Rubik", 11), justify="right")
        self.name_entry.pack(fill="x", padx=pad_x, pady=(2, 8))

        # Year selection (RTL)
        ctk.CTkLabel(self, text="اختر السنة (Year):", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(2, 0))
        existing_years = get_existing_client_years(root_path)
        if not existing_years:
            existing_years = [str(datetime.now().year)]

        self.year_combo = ctk.CTkComboBox(self, values=existing_years, command=self._on_year_changed, font=("Rubik", 11), height=32)
        self.year_combo.set(existing_years[0])
        self.year_combo.pack(fill="x", padx=pad_x, pady=(2, 8))

        # Month selection (RTL)
        ctk.CTkLabel(self, text="اختر الشهر التابع له:", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(2, 0))
        self.month_combo = ctk.CTkComboBox(self, values=["01_January"], state="readonly", font=("Rubik", 11), height=32)
        self.month_combo.pack(fill="x", padx=pad_x, pady=(2, 12))
        self._on_year_changed(existing_years[0])

        # Info Box
        info_text = (
            "سيتم إنشاء مجلد البوست مع البنية الداخلية الكاملة:\n"
            "📁 01_Sources_PSD (ملف العمل المفتوح)\n"
            "📁 02_In_Review  (التصميم قيد المراجعة)\n"
            "📁 03_Approved   (التصميم المعتمد للنشر)\n"
            "📁 00_Resources  |  📁 _TEMP"
        )
        info_box = ctk.CTkTextbox(self, height=85, font=("Rubik", 10))
        info_box.insert("1.0", info_text)
        info_box.configure(state="disabled")
        info_box.pack(fill="x", padx=pad_x, pady=(0, 15))

        # Buttons (RTL: Create on Right, Cancel on Left)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad_x, pady=(0, 15))

        cancel_btn = ctk.CTkButton(btn_frame, text="إلغاء", font=("Rubik", 11), fg_color="gray40", hover_color="gray30", command=self.destroy)
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        create_btn = ctk.CTkButton(
            btn_frame,
            text="إنشاء مجلد المشروع",
            font=("Rubik", 12, "bold"),
            command=self._create_project
        )
        create_btn.pack(side="right", fill="x", expand=True)

    def _on_year_changed(self, selected_year):
        root_path = self.client_data.get("root_path", "")
        months = get_existing_months_for_year(root_path, selected_year)
        if months:
            self.month_combo.configure(values=months)
            self.month_combo.set(months[0])
        else:
            default_m = f"{datetime.now().month:02d}_Month"
            self.month_combo.configure(values=[default_m])
            self.month_combo.set(default_m)

    def _create_project(self):
        p_name = self.name_entry.get().strip()
        if not p_name:
            return

        year = self.year_combo.get().strip()
        month = self.month_combo.get().strip()
        root_path = self.client_data.get("root_path", "")

        target_project_dir = os.path.join(root_path, year, month, p_name)
        os.makedirs(target_project_dir, exist_ok=True)

        for sub in PROJECT_SUBFOLDERS:
            os.makedirs(os.path.join(target_project_dir, sub), exist_ok=True)

        self.on_success_callback(target_project_dir)
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w = self.winfo_width() // 2
        h = self.winfo_height() // 2
        self.geometry(f"+{px - w}+{py - h}")
