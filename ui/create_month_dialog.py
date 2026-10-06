"""
ui/create_month_dialog.py
─────────────────────────
Modal dialog to create a new month structure for a selected client.
Formatted with Rubik font and RTL alignment.
"""

from datetime import datetime
import customtkinter as ctk
from core.client_manager import MONTH_NAMES, create_month_structure


class CreateMonthDialog(ctk.CTkToplevel):
    def __init__(self, parent, client_data, on_success_callback):
        super().__init__(parent)
        self.title("إنشاء دورة شهر جديد للعميل")
        self.geometry("490x400")
        self.resizable(False, False)

        self.client_data = client_data
        self.on_success_callback = on_success_callback

        self.attributes("-topmost", True)
        self.grab_set()

        self._build_ui_rtl()
        self._center(parent)

    def _build_ui_rtl(self):
        pad_x = 22
        now = datetime.now()

        # Title (RTL)
        ctk.CTkLabel(
            self,
            text=f"إنشاء هيكل الشهر لـ: {self.client_data.get('name')}",
            font=("Rubik", 14, "bold"),
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(15, 3))

        ctk.CTkLabel(
            self,
            text=f"المسار: {self.client_data.get('root_path')}",
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(0, 12))

        # Year Selection (RTL)
        ctk.CTkLabel(self, text="اختر السنة (Year):", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(3, 0))
        years = [str(now.year + i) for i in range(-2, 3)]
        self.year_combo = ctk.CTkComboBox(self, values=years, state="readonly", font=("Rubik", 11), height=32)
        self.year_combo.set(str(now.year))
        self.year_combo.pack(fill="x", padx=pad_x, pady=(2, 8))

        # Month Selection (RTL)
        ctk.CTkLabel(self, text="اختر الشهر مع الترقيم المنضبط:", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(3, 0))
        month_options = [f"{m_num:02d} - {name}" for m_num, name in MONTH_NAMES]
        self.month_combo = ctk.CTkComboBox(self, values=month_options, state="readonly", font=("Rubik", 11), height=32)
        current_month_str = next((f"{m:02d} - {n}" for m, n in MONTH_NAMES if m == now.month), month_options[0])
        self.month_combo.set(current_month_str)
        self.month_combo.pack(fill="x", padx=pad_x, pady=(2, 12))

        # Preview note
        preview_text = (
            "سيتم إنشاء خط الإنتاج المرقم التالي تلقائياً:\n"
            "📁 00_Resources\n"
            "📁 01_Sources_PSD\n"
            "📁 02_In_Review  (قيد المراجعة)\n"
            "📁 03_Approved   (التصاميم المعتمدة)\n"
            "📁 _TEMP         (ملفات مؤقتة قابلة للتنظيف)"
        )
        preview_box = ctk.CTkTextbox(self, height=95, font=("Rubik", 10))
        preview_box.insert("1.0", preview_text)
        preview_box.configure(state="disabled")
        preview_box.pack(fill="x", padx=pad_x, pady=(0, 15))

        # Buttons (RTL: Create on Right, Cancel on Left)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad_x, pady=(0, 15))

        cancel_btn = ctk.CTkButton(btn_frame, text="إلغاء", font=("Rubik", 11), fg_color="gray40", hover_color="gray30", command=self.destroy)
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        create_btn = ctk.CTkButton(
            btn_frame,
            text="إنشاء المجلدات الآن",
            font=("Rubik", 12, "bold"),
            command=self._create_month
        )
        create_btn.pack(side="right", fill="x", expand=True)

    def _create_month(self):
        try:
            year = int(self.year_combo.get())
            selected_m_str = self.month_combo.get()
            month_num = int(selected_m_str.split(" - ")[0])

            root_path = self.client_data.get("root_path")
            month_dir, created = create_month_structure(root_path, year=year, month=month_num)

            self.on_success_callback(month_dir, created)
            self.destroy()
        except Exception as e:
            print(f"Error in _create_month: {e}")

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w = self.winfo_width() // 2
        h = self.winfo_height() // 2
        self.geometry(f"+{px - w}+{py - h}")
