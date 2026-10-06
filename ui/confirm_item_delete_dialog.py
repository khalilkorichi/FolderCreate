"""
ui/confirm_item_delete_dialog.py
────────────────────────────────
Confirmation dialog for removing pinned items/favorites:
- Choice: Remove from Favorites only (إزالة من المفضلة فقط)
- Choice: Delete completely from Disk (حذف الملف/المجلد نهائياً من القرص)
"""

import os
import shutil
import customtkinter as ctk


class ConfirmItemDeleteDialog(ctk.CTkToplevel):
    def __init__(self, parent, item_data: dict, on_confirm_callback):
        super().__init__(parent)
        self.title("تأكيد حذف العنصر")
        self.geometry("490x360")
        self.resizable(False, False)

        self.item_data = item_data
        self.on_confirm_callback = on_confirm_callback

        self.attributes("-topmost", True)
        self.grab_set()

        self._build_ui_rtl()
        self._center(parent)

    def _build_ui_rtl(self):
        pad_x = 22

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=pad_x, pady=(15, 8))

        ctk.CTkLabel(
            header_frame,
            text="⚠️ تحذير: حذف العنصر",
            font=("Rubik", 15, "bold"),
            text_color="#E74C3C",
            anchor="e"
        ).pack(fill="x")

        title = self.item_data.get("title", "")
        item_path = self.item_data.get("path", "")
        is_folder = self.item_data.get("type") == "folder"

        # Item Info Card
        info_card = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray85", "gray20"))
        info_card.pack(fill="x", padx=pad_x, pady=(0, 12))

        ctk.CTkLabel(
            info_card,
            text=f"العنصر: {title} ({'مجلد' if is_folder else 'ملف'})",
            font=("Rubik", 12, "bold"),
            anchor="e"
        ).pack(fill="x", padx=12, pady=(10, 2))

        short_p = item_path if len(item_path) <= 45 else "..." + item_path[-42:]
        ctk.CTkLabel(
            info_card,
            text=f"المسار: {short_p}",
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(fill="x", padx=12, pady=(0, 10))

        # Choices
        ctk.CTkLabel(
            self,
            text="اختر نوع الحذف المطلوب:",
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(fill="x", padx=pad_x, pady=(4, 6))

        self.delete_mode_var = ctk.StringVar(value="fav_only")

        self.radio_fav = ctk.CTkRadioButton(
            self,
            text="إزالة من قائمة المفضلة فقط (الملف سيبقى محفوظاً على جهازك)",
            variable=self.delete_mode_var,
            value="fav_only",
            font=("Rubik", 11)
        )
        self.radio_fav.pack(fill="x", padx=pad_x, pady=4, anchor="e")

        self.radio_disk = ctk.CTkRadioButton(
            self,
            text="حذف الملف/المجلد نهائياً من القرص الصلب",
            variable=self.delete_mode_var,
            value="delete_disk",
            font=("Rubik", 11),
            text_color="#E74C3C"
        )
        self.radio_disk.pack(fill="x", padx=pad_x, pady=4, anchor="e")

        # Buttons (RTL: Cancel on Left, Confirm on Right)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad_x, pady=(18, 15))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="إلغاء",
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
        delete_from_disk = (self.delete_mode_var.get() == "delete_disk")
        path = self.item_data.get("path", "")

        disk_deleted = False
        if delete_from_disk and path and os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=False)
                else:
                    os.remove(path)
                disk_deleted = True
            except Exception as e:
                print(f"[confirm_item_delete] Error deleting from disk: {e}")

        self.on_confirm_callback(self.item_data, delete_from_disk, disk_deleted)
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w = self.winfo_width() // 2
        h = self.winfo_height() // 2
        self.geometry(f"+{px - w}+{py - h}")
