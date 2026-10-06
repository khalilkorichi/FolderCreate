"""
core/dnd_helper.py
──────────────────
Helper utilities for drag-and-drop parsing and safe registration.
Extracts dropped files and directory paths correctly across Windows Explorer drops.
"""

import os
from typing import List


def parse_dropped_paths(event_data: str, tk_root) -> List[str]:
    """
    Parses the raw dropped files string from TkinterDnD.
    Handles spaces, braces, and relative separators safely.
    """
    if not event_data:
        return []

    try:
        raw_items = tk_root.tk.splitlist(event_data)
    except Exception:
        raw_items = event_data.split()

    clean_paths = []
    for item in raw_items:
        clean = item.strip("{}").strip('"').strip("'").strip()
        clean = os.path.normpath(clean)
        if os.path.exists(clean):
            clean_paths.append(clean)

    return clean_paths
