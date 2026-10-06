"""
core/path_manager.py
────────────────────
Handles persistence of the user's preferred root directory.

All logic is pure (no UI calls), making it safe to unit-test independently.
"""

import os

# ── Constants ──────────────────────────────────────────────────────────────────
DEFAULT_PATH_FILE = "default_path.txt"
FALLBACK_DEFAULT_PATH = "X:/Geteilte Ablagen/"  # Hardcoded last-resort default


def load_default_path() -> str:
    """
    Returns the saved default path from *default_path.txt*.
    Falls back to FALLBACK_DEFAULT_PATH when the file is missing
    or the stored path is no longer a valid directory.
    """
    try:
        with open(DEFAULT_PATH_FILE, "r") as f:
            path = f.read().strip()
            if os.path.isdir(path):
                return path
    except FileNotFoundError:
        pass  # First run — file doesn't exist yet
    return FALLBACK_DEFAULT_PATH


def save_default_path(path: str) -> bool:
    """
    Persists *path* to *default_path.txt*.

    Returns:
        True  – written successfully.
        False – an OS-level error occurred (printed to stderr).
    """
    try:
        with open(DEFAULT_PATH_FILE, "w") as f:
            f.write(path)
        return True
    except Exception as e:
        print(f"[path_manager] Error saving default path: {e}")
        return False
