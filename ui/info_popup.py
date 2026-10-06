"""
ui/info_popup.py
────────────────
A reusable modal-like popup window used to surface status messages
(success, warning, error) to the user.
Formatted with Rubik font and RTL alignment.
"""

import customtkinter as ctk


class InfoPopup:
    """
    A hidden CTkToplevel that is revealed (via `.show()`) whenever the
    application needs to communicate a status message.
    """

    _COLORS = {
        "success": "#2ECC71",
        "warning": "#F39C12",
        "error":   "#E74C3C",
        "info":    ("gray70", "gray90"),
    }

    def __init__(self, parent: ctk.CTk):
        self._parent = parent

        self._window = ctk.CTkToplevel(parent)
        self._window.title("تنبيه")
        self._window.geometry("320x160")
        self._window.resizable(False, False)
        self._window.withdraw()

        self._window.protocol("WM_DELETE_WINDOW", self._window.withdraw)

        frame = ctk.CTkFrame(self._window)
        frame.pack(expand=True, fill="both", padx=15, pady=15)

        self._label = ctk.CTkLabel(frame, text="", wraplength=280, font=("Rubik", 11), justify="center")
        self._label.pack(expand=True, fill="both", pady=8)

        ok_btn = ctk.CTkButton(frame, text="حسناً", font=("Rubik", 11, "bold"), width=90, command=self._window.withdraw)
        ok_btn.pack(pady=8)

    def show(self, message: str, level: str = "info") -> None:
        color = self._COLORS.get(level, self._COLORS["info"])
        self._label.configure(text=message, text_color=color)
        self._window.deiconify()
        self._center_on_parent()

    def _center_on_parent(self) -> None:
        self._window.update_idletasks()
        px = self._parent.winfo_x() + self._parent.winfo_width() // 2
        py = self._parent.winfo_y() + self._parent.winfo_height() // 2
        pw = self._window.winfo_width() // 2
        ph = self._window.winfo_height() // 2
        self._window.geometry(f"+{px - pw}+{py - ph}")
