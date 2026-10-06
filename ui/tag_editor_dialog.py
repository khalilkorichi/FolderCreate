"""
ui/tag_editor_dialog.py
───────────────────────
Custom Design Tagging Dialog:
- Fully aligned to Rubik font & Right-To-Left (RTL) standards.
- Quick preset buttons for instant social media & marketing tags.
- Free-form text entry for custom designer tags.
- Option to reset back to automatic dimension-based tag.
"""

import customtkinter as ctk
from typing import Callable, Optional


class TagEditorDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        filename: str,
        dimensions_str: str,
        current_tag: str,
        on_save: Callable[[str], None]
    ):
        super().__init__(parent)
        self.on_save = on_save
        self.result_tag: Optional[str] = None

        self.title("🏷️ تعديل وتصنيف وسم التصميم")
        self.geometry("480x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        try:
            px = parent.winfo_rootx() + (parent.winfo_width() // 2) - 240
            py = parent.winfo_rooty() + (parent.winfo_height() // 2) - 210
            self.geometry(f"+{max(0, px)}+{max(0, py)}")
        except Exception:
            pass

        self._build_ui(filename, dimensions_str, current_tag)

    def _build_ui(self, filename: str, dimensions_str: str, current_tag: str):
        pad_frame = ctk.CTkFrame(self, fg_color="transparent")
        pad_frame.pack(fill="both", expand=True, padx=20, pady=18)

        # Header info (RTL)
        ctk.CTkLabel(
            pad_frame,
            text="🏷️ تخصيص وسم التصميم",
            font=("Rubik", 15, "bold"),
            anchor="e"
        ).pack(fill="x", anchor="e", pady=(0, 4))

        meta_frame = ctk.CTkFrame(pad_frame, fg_color=("gray90", "gray20"), corner_radius=8)
        meta_frame.pack(fill="x", pady=(0, 14), padx=2)

        inner_meta = ctk.CTkFrame(meta_frame, fg_color="transparent")
        inner_meta.pack(fill="x", padx=12, pady=10)

        # Truncate filename if needed
        disp_name = filename if len(filename) <= 38 else filename[:35] + "..."
        ctk.CTkLabel(
            inner_meta,
            text=f"الملف: {disp_name}",
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(fill="x", anchor="e")

        ctk.CTkLabel(
            inner_meta,
            text=f"الأبعاد المقاسة: {dimensions_str} | الوسم الحالي: {current_tag}",
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(fill="x", anchor="e", pady=(3, 0))

        # Presets section
        ctk.CTkLabel(
            pad_frame,
            text="اختر وسماً سريعاً أو اكتب وسماً مخصصاً:",
            font=("Rubik", 11, "bold"),
            anchor="e"
        ).pack(fill="x", anchor="e", pady=(0, 6))

        presets_box = ctk.CTkFrame(pad_frame, fg_color="transparent")
        presets_box.pack(fill="x", pady=(0, 10))

        presets = [
            ("📱 ستوري / ريلز", "ستوري / ريلز (9:16)"),
            ("📸 منشور إنستغرام", "منشور إنستغرام / إعلاني (4:5)"),
            ("⏹️ منشور مربع", "منشور مربع (1:1)"),
            ("🌐 إعلان ممول", "إعلان ممول / بانر (1.91:1)"),
            ("🖥️ يوتيوب / شاشة", "شاشة كاملة / يوتيوب (16:9)"),
            ("🎨 هوية بصرية", "هوية بصرية / شعار"),
            ("📑 مطبوعات / بروشور", "مطبوعات / بروشور"),
            ("🔄 وسم تلقائي", "")
        ]

        # 2 rows of 4 columns
        for idx, (label_btn, val_tag) in enumerate(presets):
            r = idx // 4
            c = 3 - (idx % 4)  # RTL column ordering
            btn = ctk.CTkButton(
                presets_box,
                text=label_btn,
                font=("Rubik", 10),
                height=28,
                fg_color=("gray80", "gray25"),
                hover_color=("gray70", "gray35"),
                command=lambda v=val_tag: self._select_preset(v)
            )
            presets_box.grid_columnconfigure(c, weight=1)
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="ew")

        # Custom text input
        ctk.CTkLabel(
            pad_frame,
            text="الوسم المخصص (أو اتركه فارغاً للاعتماد على القياس التلقائي):",
            font=("Rubik", 10),
            text_color="gray70",
            anchor="e"
        ).pack(fill="x", anchor="e", pady=(6, 3))

        clean_initial = current_tag.replace("🏷️", "").strip() if "🏷️" in current_tag else current_tag
        self.tag_entry = ctk.CTkEntry(
            pad_frame,
            font=("Rubik", 11),
            placeholder_text="مثال: ستوري عرض الصيف، بانر سناب شات...",
            height=34,
            justify="right"
        )
        self.tag_entry.pack(fill="x", pady=(0, 18))
        if clean_initial and not clean_initial.startswith("📁") and not clean_initial.startswith("🎨"):
            self.tag_entry.insert(0, clean_initial)

        # Action Buttons
        btn_row = ctk.CTkFrame(pad_frame, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="إلغاء",
            font=("Rubik", 11),
            width=90,
            height=32,
            fg_color="gray50",
            hover_color="gray40",
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_row,
            text="💾 حفظ الوسم",
            font=("Rubik", 11, "bold"),
            width=120,
            height=32,
            fg_color="#27AE60",
            hover_color="#1E8449",
            command=self._save_and_close
        )
        save_btn.pack(side="right")

    def _select_preset(self, tag_val: str):
        self.tag_entry.delete(0, "end")
        if tag_val:
            self.tag_entry.insert(0, tag_val)

    def _save_and_close(self):
        entered = self.tag_entry.get().strip()
        self.on_save(entered)
        self.destroy()
