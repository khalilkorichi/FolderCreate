"""
core/font_loader.py
───────────────────
Registers embedded fonts (e.g., Rubik) dynamically into the Windows GDI font table
so that Tkinter and CustomTkinter can render them without requiring system-wide installation.
"""

import ctypes
import os
import sys

FR_PRIVATE = 0x10
FR_NOT_ENUM = 0x20

_LOADED_FONTS = []


def load_embedded_fonts() -> bool:
    """
    Scans `assets/fonts` and registers any .ttf / .otf files using GDI.
    Returns True if at least one font was successfully registered.
    """
    if sys.platform != "win32":
        return False

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "assets", "fonts")

    if not os.path.exists(fonts_dir):
        return False

    success = False
    for filename in os.listdir(fonts_dir):
        if filename.lower().endswith((".ttf", ".otf")):
            font_path = os.path.abspath(os.path.join(fonts_dir, filename))
            try:
                # AddFontResourceExW registers the font for the current process session
                num_added = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
                if num_added > 0:
                    _LOADED_FONTS.append(font_path)
                    success = True
            except Exception as e:
                print(f"[font_loader] Failed to load {filename}: {e}")

    return success
