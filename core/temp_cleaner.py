"""
core/temp_cleaner.py
────────────────────
Scans client directories for `_TEMP` / `_TEMP_SCRATCH` folders.
Calculates size and file count, and provides safe purging / deletion.
"""

import os
import shutil
from typing import Any, Dict, List


def scan_temp_folders(root_dir: str) -> List[Dict[str, Any]]:
    """
    Recursively scans `root_dir` for folders named '_TEMP' or starting with '_TEMP'.
    Returns details: folder path, total files, total size in MB, and relative location.
    """
    results = []
    if not os.path.exists(root_dir):
        return results

    for root, dirs, _ in os.walk(root_dir):
        # Identify matching temp folders at current level
        matching_temps = [d for d in dirs if d.upper() == "_TEMP" or d.upper().startswith("_TEMP")]
        for d in matching_temps:
            temp_path = os.path.join(root, d)
            size_bytes, file_count = _get_folder_stats(temp_path)
            results.append({
                "path": temp_path,
                "name": d,
                "file_count": file_count,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "parent_dir": os.path.basename(root)
            })
            # Prune directory from dirs list so os.walk does not descend into it recursively
            if d in dirs:
                dirs.remove(d)
    return results


def _get_folder_stats(folder_path: str) -> tuple[int, int]:
    total_size = 0
    total_files = 0
    try:
        for root, _, files in os.walk(folder_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                    total_files += 1
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
    return total_size, total_files


def clear_temp_folder(folder_path: str, keep_folder: bool = True) -> bool:
    """
    Purges contents of the temporary directory.
    If `keep_folder` is True, removes inner contents and keeps the empty `_TEMP` directory.
    """
    if not os.path.exists(folder_path):
        return False

    try:
        if keep_folder:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    try:
                        os.remove(item_path)
                    except Exception:
                        pass
        else:
            shutil.rmtree(folder_path, ignore_errors=True)
        return True
    except Exception as e:
        print(f"[temp_cleaner] Error cleaning {folder_path}: {e}")
        return False
