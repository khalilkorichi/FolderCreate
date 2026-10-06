"""
ui/preview_window.py
────────────────────
Displays a read-only tree of the folder structure that would be created by the template.
Formatted with Rubik font and Arabic controls.
"""

import customtkinter as ctk
from core.template_engine import load_template_file, generate_paths, format_paths_as_tree


class PreviewWindow:
    def __init__(self, parent: ctk.CTk):
        self._parent = parent

        self._window = ctk.CTkToplevel(parent)
        self._window.title("معاينة هيكل شجرة المجلدات")
        self._window.geometry("520x420")
        self._window.resizable(False, False)
        self._window.withdraw()
        self._window.protocol("WM_DELETE_WINDOW", self._window.withdraw)

        frame = ctk.CTkFrame(self._window)
        frame.pack(expand=True, fill="both", padx=15, pady=15)

        self._textbox = ctk.CTkTextbox(frame, wrap="none", font=("Consolas", 11))
        self._textbox.pack(expand=True, fill="both", pady=(5, 10))

        ok_btn = ctk.CTkButton(frame, text="إغلاق المعاينة", font=("Rubik", 11, "bold"), width=110, command=self._window.withdraw)
        ok_btn.pack(pady=5)

    def show(self, root_path: str, template_file_path: str) -> None:
        self._set_text("جاري توليد شجرة المعاينة...")
        self._window.deiconify()

        data, error = load_template_file(template_file_path)
        if error:
            self._set_text(f"خطأ أثناء قراءة القالب:\n{error}")
            return
        if data is None:
            self._set_text("ملف القالب فارغ.")
            return

        paths = generate_paths(data)
        if not paths:
            self._set_text("القالب صالح لكنه لا يحتوي على أي مجلدات.")
            return

        tree = format_paths_as_tree(paths, root_path)
        self._set_text(tree)
        self._center_on_parent()

    def _set_text(self, content: str) -> None:
        self._textbox.delete("1.0", ctk.END)
        self._textbox.insert("1.0", content)

    def _center_on_parent(self) -> None:
        self._window.update_idletasks()
        px = self._parent.winfo_x() + self._parent.winfo_width() // 2
        py = self._parent.winfo_y() + self._parent.winfo_height() // 2
        pw = self._window.winfo_width() // 2
        ph = self._window.winfo_height() // 2
        self._window.geometry(f"+{px - pw}+{py - ph}")
