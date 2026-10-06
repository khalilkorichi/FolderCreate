"""
ui/add_client_dialog.py
───────────────────────
Dialog window to register a new client:
- Select the parent 'Clients Base Directory' (مجلد العملاء الأساسي).
- Enter Client Name and Client Code.
- Automatically creates: [Base_Directory] / [Client_Name] (مجلد باسم العميل داخل مجلد العملاء).
- Generates _Brand_Assets inside the client's own folder.
- Formatted with Rubik font and RTL orientation.
"""

import os
import re
import customtkinter as ctk
from tkinter import filedialog
from core.client_manager import init_client_brand_assets
from core.path_manager import load_default_path


def sanitize_folder_name(name: str) -> str:
    """Removes invalid characters for Windows folder names."""
    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()


class AddClientDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.title("إضافة عميل جديد إلى مساحة العمل")
        self.geometry("540x510")
        self.resizable(False, False)
        self.on_save_callback = on_save_callback

        self.attributes("-topmost", True)
        self.grab_set()

        self._build_ui_rtl()
        self._center(parent)

    def _build_ui_rtl(self):
        pad_x = 22

        # Title
        ctk.CTkLabel(
            self,
            text="إضافة عميل جديد لمساحة العمل",
            font=("Rubik", 15, "bold"),
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(15, 8))

        # 1. Base Directory (مجلد العملاء الأساسي)
        ctk.CTkLabel(
            self,
            text="مجلد العملاء الأساسي (المكان الذي يضم كل العملاء):",
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(2, 0))

        base_frame = ctk.CTkFrame(self, fg_color="transparent")
        base_frame.pack(fill="x", padx=pad_x, pady=(2, 6))

        browse_base_btn = ctk.CTkButton(
            base_frame, text="استعراض", font=("Rubik", 11), width=80, command=self._browse_base_dir
        )
        browse_base_btn.pack(side="left")

        self.base_dir_entry = ctk.CTkEntry(
            base_frame,
            placeholder_text="اختر مجلد 'العملاء' الأساسي...",
            font=("Rubik", 11),
            justify="right"
        )
        self.base_dir_entry.pack(side="right", fill="x", expand=True, padx=(8, 0))
        # Pre-fill with default path
        self.base_dir_entry.insert(0, load_default_path())
        self.base_dir_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        # 2. Client Name (اسم العميل)
        ctk.CTkLabel(self, text="اسم العميل الكامل:", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(4, 0))
        self.name_entry = ctk.CTkEntry(
            self,
            placeholder_text="مثال: شركة الأفق للتصميم",
            font=("Rubik", 11),
            justify="right"
        )
        self.name_entry.pack(fill="x", padx=pad_x, pady=(2, 6))
        self.name_entry.bind("<KeyRelease>", lambda e: self._on_name_changed())

        # 3. Client Code (رمز العميل)
        ctk.CTkLabel(self, text="رمز العميل المختصر (Code):", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(2, 0))
        self.code_entry = ctk.CTkEntry(self, placeholder_text="مثال: OFQ أو CLT-01", font=("Rubik", 11), justify="right")
        self.code_entry.pack(fill="x", padx=pad_x, pady=(2, 6))

        # 4. Preview Target Folder Path (معاينة مسار مجلد العميل النهائي)
        self.preview_lbl = ctk.CTkLabel(
            self,
            text="📁 المسار النهائي للمجلد: سيتم إنشاؤه تلقائياً باسم العميل",
            font=("Rubik", 10),
            text_color="#3498DB",
            anchor="e"
        )
        self.preview_lbl.pack(fill="x", padx=pad_x, pady=(2, 6))

        # 5. Logo Path (شعار العميل)
        ctk.CTkLabel(self, text="شعار العميل (Logo - اختياري):", font=("Rubik", 11, "bold"), anchor="e").pack(fill="x", padx=pad_x, pady=(2, 0))
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=pad_x, pady=(2, 6))

        browse_logo_btn = ctk.CTkButton(logo_frame, text="اختيار صورة", font=("Rubik", 11), width=80, command=self._browse_logo)
        browse_logo_btn.pack(side="left")

        self.logo_entry = ctk.CTkEntry(logo_frame, placeholder_text="اختر صورة الشعار (PNG, JPG)...", font=("Rubik", 11), justify="right")
        self.logo_entry.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 6. Checkbox to init _Brand_Assets
        self.init_brand_var = ctk.BooleanVar(value=True)
        self.init_brand_chk = ctk.CTkCheckBox(
            self,
            text="إنشاء مجلدات الهوية البصرية تلقائياً داخل مجلد العميل (_Brand_Assets)",
            font=("Rubik", 11),
            variable=self.init_brand_var
        )
        self.init_brand_chk.pack(fill="x", padx=pad_x, pady=(6, 8))

        # Status Label
        self.status_lbl = ctk.CTkLabel(self, text="", font=("Rubik", 10), text_color="red", anchor="e")
        self.status_lbl.pack(fill="x", padx=pad_x, pady=(0, 4))

        # Buttons (RTL: Save on Right, Cancel on Left)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad_x, pady=(0, 15))

        cancel_btn = ctk.CTkButton(btn_frame, text="إلغاء", font=("Rubik", 11), fg_color="gray40", hover_color="gray30", command=self.destroy)
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        save_btn = ctk.CTkButton(btn_frame, text="إنشاء وحفظ العميل", font=("Rubik", 12, "bold"), command=self._save_client)
        save_btn.pack(side="right", fill="x", expand=True)

        self._update_preview()

    def _browse_base_dir(self):
        dir_selected = filedialog.askdirectory(title="اختر مجلد 'العملاء' الأساسي")
        if dir_selected:
            self.base_dir_entry.delete(0, ctk.END)
            self.base_dir_entry.insert(0, dir_selected)
            self._update_preview()

    def _browse_logo(self):
        file_selected = filedialog.askopenfilename(
            title="اختر شعار العميل",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.ico")]
        )
        if file_selected:
            self.logo_entry.delete(0, ctk.END)
            self.logo_entry.insert(0, file_selected)

    def _on_name_changed(self):
        name = self.name_entry.get().strip()
        # Guess code if code entry is empty
        if name and not self.code_entry.get().strip():
            words = name.split()
            code_guess = "".join(w[0] for w in words[:3]).upper() if words else "CLT"
            self.code_entry.delete(0, ctk.END)
            self.code_entry.insert(0, code_guess)
        self._update_preview()

    def _update_preview(self):
        base_dir = self.base_dir_entry.get().strip()
        client_name = sanitize_folder_name(self.name_entry.get().strip())
        if base_dir and client_name:
            target_path = os.path.join(base_dir, client_name)
            self.preview_lbl.configure(text=f"📁 سيتم الإنشاء في: {target_path}")
        elif base_dir:
            self.preview_lbl.configure(text=f"📁 سيتم إنشاء مجلد جديد باسم العميل داخل: {base_dir}")
        else:
            self.preview_lbl.configure(text="📁 يرجى تحديد المجلد الأساسي واسم العميل")

    def _save_client(self):
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        base_dir = self.base_dir_entry.get().strip()
        logo = self.logo_entry.get().strip()

        if not base_dir:
            self.status_lbl.configure(text="يرجى تحديد مجلد العملاء الأساسي.")
            return

        if not name:
            self.status_lbl.configure(text="يرجى كتابة اسم العميل.")
            return

        clean_name = sanitize_folder_name(name)
        if not clean_name:
            self.status_lbl.configure(text="اسم العميل غير صالح لتسمية المجلد.")
            return

        # Target: [base_dir] / [clean_name]
        client_folder_path = os.path.join(base_dir, clean_name)

        try:
            # 1. Ensure base directory and client-specific directory exist
            os.makedirs(client_folder_path, exist_ok=True)

            # 2. Optionally create _Brand_Assets inside the client folder
            if self.init_brand_var.get():
                init_client_brand_assets(client_folder_path)

            self.on_save_callback(name=name, code=code, root_path=client_folder_path, logo_path=logo)
            self.destroy()
        except Exception as e:
            self.status_lbl.configure(text=f"خطأ أثناء إنشاء مجلد العميل: {e}")

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w = self.winfo_width() // 2
        h = self.winfo_height() // 2
        self.geometry(f"+{px - w}+{py - h}")
