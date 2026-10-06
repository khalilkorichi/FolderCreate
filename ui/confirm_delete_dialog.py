"""
ui/confirm_delete_dialog.py
───────────────────────────
Modal confirmation dialog for deleting a client:
- Option 1: Remove from App only (إلغاء الإدراج من البرنامج فقط مع بقاء المجلد على القرص).
- Option 2: Completely delete from Disk (حذف المجلد نهائياً مع كافة ملفاته من القرص).
- Red alert warning with confirmation buttons.
"""

import os
import shutil
import customtkinter as ctk


class ConfirmDeleteDialog(ctk.CTkToplevel):
    def __init__(self, parent, client_data: dict, on_confirm_callback):
        super().__init__(parent)
        self.title("تأكيد حذف العميل ومساحة العمل")
        self.geometry("500x380")
        self.resizable(False, False)

        self.client_data = client_data
        self.on_confirm_callback = on_confirm_callback

        self.attributes("-topmost", True)
        self.grab_set()

        self._build_ui_rtl()
        self._center(parent)

    def _build_ui_rtl(self):
        pad_x = 24

        # Warning Icon & Title
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=pad_x, pady=(15, 8))

        ctk.CTkLabel(
            header_frame,
            text="⚠️ تحذير: حذف العميل من النظام",
            font=("Rubik", 15, "bold"),
            text_color="#E74C3C",
            anchor="e"
        ).pack(fill="x")

        client_name = self.client_data.get("name", "")
        root_path = self.client_data.get("root_path", "")

        # Target Client Details Card
        info_card = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray85", "gray20"))
        info_card.pack(fill="x", padx=pad_x, pady=(0, 12))

        ctk.CTkLabel(
            info_card,
            text=f"العميل المستهدف: {client_name}",
            font=("Rubik", 12, "bold"),
            anchor="e"
        ).pack(fill="x", padx=12, pady=(10, 2))

        short_p = root_path if len(root_path) <= 45 else "..." + root_path[-42:]
        ctk.CTkLabel(
            info_card,
            text=f"المسار: {short_p}",
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(fill="x", padx=12, pady=(0, 10))

        # Radio Options Choice (حذف من البرنامج فقط أم حذف من القرص)
        ctk.CTkLabel(
            self,
            text="اختر نوع عملية الحذف:",
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(4, 6))

        self.delete_mode_var = ctk.StringVar(value="app_only")

        self.radio_app = ctk.CTkRadioButton(
            self,
            text="حذف من البرنامج فقط (إبقاء المجلد والملفات محفوظة في جهازك)",
            variable=self.delete_mode_var,
            value="app_only",
            font=("Rubik", 11)
        )
        self.radio_app.pack(fill="x", padx=pad_x, pady=4, anchor="e")

        self.radio_disk = ctk.CTkRadioButton(
            self,
            text="حذف المجلد كلياً من القرص (حذف نهائي للمجلد بكافة ملفاته وتصاميمه)",
            variable=self.delete_mode_var,
            value="delete_disk",
            font=("Rubik", 11),
            text_color="#E74C3C"
        )
        self.radio_disk.pack(fill="x", padx=pad_x, pady=4, anchor="e")

        # Warning Note
        self.warn_lbl = ctk.CTkLabel(
            self,
            text="* تنبيه: خيار الحذف الكلي من القرص لا يمكن التراجع عنه وسيتم مسح المجلد نهائياً.",
            font=("Rubik", 9),
            text_color="gray60",
            anchor="e"
        )
        self.warn_lbl.pack(fill="x", padx=pad_x, pady=(10, 15))

        # Buttons (RTL: Cancel on Left, Delete on Right)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad_x, pady=(0, 15))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="إلغاء التراجع",
            font=("Rubik", 11),
            fg_color="gray40",
            hover_color="gray30",
            command=self.destroy
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="تأكيد الحذف 🗑️",
            font=("Rubik", 12, "bold"),
            fg_color="#C0392B",
            hover_color="#922B21",
            command=self._execute_delete
        )
        confirm_btn.pack(side="right", fill="x", expand=True)

    def _execute_delete(self):
        mode = self.delete_mode_var.get()
        delete_from_disk = (mode == "delete_disk")
        root_path = self.client_data.get("root_path", "")

        disk_deleted = False
        if delete_from_disk:
            if root_path and os.path.exists(root_path):
                try:
                    shutil.rmtree(root_path, ignore_errors=False)
                    disk_deleted = True
                except Exception as e:
                    print(f"[confirm_delete] Error deleting folder from disk: {e}")
                    # If failed, still let callback handle app record

        self.on_confirm_callback(self.client_data, delete_from_disk, disk_deleted)
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w = self.winfo_width() // 2
        h = self.winfo_height() // 2
        self.geometry(f"+{px - w}+{py - h}")
