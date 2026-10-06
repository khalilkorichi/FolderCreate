"""
main.py
───────
Entry point for FolderCreate.

Run directly:
    python main.py

Or package with auto-py-to-exe pointing to this file instead of FolderCreate.py.
"""

from ui.app_window import AppWindow


if __name__ == "__main__":
    app = AppWindow()
    app.run()
