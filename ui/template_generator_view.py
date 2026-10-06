"""
ui/template_generator_view.py
─────────────────────────────
The original FolderCreate template generator:
- Formatted with Rubik typography and RTL alignment.
- Supports Drag-and-Drop: drop any folder directly onto the path entry or drop zone
  to set it as target folder immediately.
- Directory selection, template combobox, preview and creation.
"""

import os
import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from core.path_manager import load_default_path, save_default_path
from core.template_engine import (
    load_templates,
    load_template_file,
    generate_paths,
    create_folders_from_paths,
)
from core.dnd_helper import parse_dropped_paths
from ui.preview_window import PreviewWindow


TEMPLATE_PATH = os.path.join(os.getcwd(), "templates")


class TemplateGeneratorView(ctk.CTkFrame):
    def __init__(self, parent, notify_callback):
        super().__init__(parent, fg_color="transparent")
        self.notify = notify_callback
        self._preview_win = PreviewWindow(self.winfo_toplevel())

        self._build_ui_rtl()
        self._load_templates()

    def _build_ui_rtl(self):
        # Header (RTL)
        ctk.CTkLabel(
            self,
            text="📁 منشئ هياكل المجلدات بالقوالب",
            font=("Rubik", 17, "bold"),
            anchor="e"
        ).pack(fill="x", padx=20, pady=(15, 8))

        # Directory Selection Frame (RTL: Browse & Set Default on Left, Entry on Right)
        dir_frame = ctk.CTkFrame(self)
        dir_frame.pack(fill="x", padx=20, pady=(0, 10))
        dir_frame.grid_columnconfigure(0, weight=1)

        self._path_entry = ctk.CTkEntry(
            dir_frame,
            placeholder_text="اختر أو اسحب المجلد الرئيسي لتوليد الهيكل هنا...",
            font=("Rubik", 11),
            justify="right"
        )
        self._path_entry.grid(row=0, column=0, padx=(10, 10), pady=12, sticky="ew")
        self._path_entry.insert(0, load_default_path())

        browse_btn = ctk.CTkButton(dir_frame, text="استعراض", font=("Rubik", 11), width=80, command=self._browse_directory)
        browse_btn.grid(row=0, column=1, pady=12, padx=(0, 6))

        set_default_btn = ctk.CTkButton(
            dir_frame, text="تعيين كافتراضي", font=("Rubik", 11), width=95, command=self._set_default_path
        )
        set_default_btn.grid(row=0, column=2, padx=(0, 10), pady=12)

        # Drag and Drop support on Path Entry & Frame
        if DND_AVAILABLE:
            try:
                self._path_entry.drop_target_register(DND_FILES)
                self._path_entry.dnd_bind("<<Drop>>", self._on_drop_target)
                dir_frame.drop_target_register(DND_FILES)
                dir_frame.dnd_bind("<<Drop>>", self._on_drop_target)
            except Exception as e:
                print(f"[template_generator] DnD warning: {e}")

        # Template Selection
        ctk.CTkLabel(self, text="اختر القالب (Template):", anchor="e", font=("Rubik", 12, "bold")).pack(
            fill="x", padx=20, pady=(5, 5)
        )

        self._template_combo = ctk.CTkComboBox(self, state="readonly", height=36, font=("Rubik", 12))
        self._template_combo.pack(fill="x", padx=20, pady=(0, 15))

        # Preview Button
        self._preview_btn = ctk.CTkButton(
            self,
            text="👁️ معاينة الشجرة قبل الإنشاء (Preview)",
            command=self._show_preview,
            height=36,
            font=("Rubik", 12),
            fg_color=("gray50", "gray30"),
            hover_color=("gray40", "gray20"),
        )
        self._preview_btn.pack(fill="x", padx=20, pady=(5, 10))

        # Create Folders Button
        self._create_btn = ctk.CTkButton(
            self,
            text="🚀 إنشاء المجلدات الآن",
            command=self._create_folders,
            height=42,
            font=("Rubik", 14, "bold"),
        )
        self._create_btn.pack(fill="x", padx=20, pady=(5, 20))

    def _on_drop_target(self, event):
        paths = parse_dropped_paths(event.data, self.winfo_toplevel())
        if paths:
            target = paths[0]
            if os.path.isfile(target):
                target = os.path.dirname(target)
            self._path_entry.delete(0, ctk.END)
            self._path_entry.insert(0, target)
            self.notify(f"تم تعيين مسار المجلد المستهدف:\n{target}", level="success")

    def _load_templates(self):
        templates = load_templates(TEMPLATE_PATH)
        if templates:
            self._template_combo.configure(values=templates)
            self._template_combo.set(templates[0])
        else:
            self._template_combo.set("لا توجد قوالب متاحة")
            self._template_combo.configure(state="disabled")
            self._create_btn.configure(state="disabled")
            self._preview_btn.configure(state="disabled")

    def _browse_directory(self):
        directory = ctk.filedialog.askdirectory(initialdir=self._path_entry.get())
        if directory:
            self._path_entry.delete(0, ctk.END)
            self._path_entry.insert(0, directory)

    def _set_default_path(self):
        path = self._path_entry.get()
        if not os.path.isdir(path):
            self.notify("المسار غير صالح. يرجى اختيار مجلد حقيقي.", level="warning")
            return
        if save_default_path(path):
            self.notify(f"تم حفظ المسار الافتراضي بنجاح:\n{path}", level="success")
        else:
            self.notify("فشل حفظ المسار الافتراضي.", level="error")

    def _show_preview(self):
        template_path = os.path.join(TEMPLATE_PATH, self._template_combo.get())
        self._preview_win.show(self._path_entry.get(), template_path)

    def _create_folders(self):
        root_path = self._path_entry.get()
        template_name = self._template_combo.get()
        template_path = os.path.join(TEMPLATE_PATH, template_name)

        data, error = load_template_file(template_path)
        if error:
            self.notify(error, level="error")
            return
        if data is None:
            self.notify("ملف القالب فارغ.", level="warning")
            return

        paths = generate_paths(data)
        if not paths:
            self.notify("القالب صالح لكنه لا يحتوي على أي مجلدات.", level="warning")
            return

        result = create_folders_from_paths(root_path, paths)
        if result.success:
            self.notify(f"تم إنشاء {result.total} مجلد(اً) بنجاح!", level="success")
        else:
            self.notify(f"حدث خطأ أثناء الإنشاء ({len(result.errors)} أخطاء).", level="error")
