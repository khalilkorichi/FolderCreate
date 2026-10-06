"""
core/template_engine.py
───────────────────────
Everything related to YAML templates:

  • Discovering template files on disk.
  • Parsing YAML into a flat list of relative directory paths.
  • Creating the real directories on disk.
  • Rendering a human-readable tree string for the preview window.

All functions are pure / side-effect-free except `create_folders_from_template`,
which deliberately writes to the filesystem.
"""

import os
import yaml
from typing import Optional


# ── Template Discovery ─────────────────────────────────────────────────────────

def load_templates(template_dir: str) -> list[str]:
    """
    Scans *template_dir* for `.yaml` / `.yml` files.

    Returns:
        A sorted list of filenames (not full paths).
        An empty list when the directory is missing or unreadable.
    """
    if not os.path.isdir(template_dir):
        return []
    try:
        return sorted(
            f for f in os.listdir(template_dir)
            if f.endswith((".yaml", ".yml"))
        )
    except OSError as e:
        print(f"[template_engine] Cannot read template directory '{template_dir}': {e}")
        return []


# ── YAML → Path List ───────────────────────────────────────────────────────────

def generate_paths(data, current_path: str = "") -> list[str]:
    """
    Recursively traverses the YAML structure and returns a flat list of
    relative directory paths to be created.

    Supports both dict-style nesting and list-style nesting (as used in the
    existing templates).  Pure — no side effects.

    Args:
        data:         Parsed YAML object (dict, list, or scalar).
        current_path: Accumulated relative path during recursion.

    Returns:
        List of relative path strings (using ``os.sep`` as separator).
    """
    paths: list[str] = []

    if isinstance(data, dict):
        for key, value in data.items():
            paths.extend(generate_paths(value, os.path.join(current_path, str(key))))

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    paths.extend(
                        generate_paths(value, os.path.join(current_path, str(key)))
                    )
            else:
                paths.append(os.path.join(current_path, str(item)))

    return paths


def load_template_file(template_file_path: str) -> tuple[Optional[object], Optional[str]]:
    """
    Reads and parses a single YAML template file.

    Returns:
        (data, None)         – on success.
        (None, error_message) – when the file is missing or malformed.
    """
    try:
        with open(template_file_path, "r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        return data, None
    except FileNotFoundError:
        return None, f"Template file not found: '{os.path.basename(template_file_path)}'"
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    except Exception as e:
        return None, f"Unexpected error reading template: {e}"


# ── Folder Creation ────────────────────────────────────────────────────────────

class FolderCreationResult:
    """Value object returned by ``create_folders_from_paths``."""

    def __init__(self):
        self.created: list[str] = []
        self.errors: list[tuple[str, str]] = []  # (path, error_message)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total(self) -> int:
        return len(self.created) + len(self.errors)


def create_folders_from_paths(root_path: str, relative_paths: list[str]) -> FolderCreationResult:
    """
    Creates all directories under *root_path* using the given relative paths.

    Uses ``os.makedirs(..., exist_ok=True)`` so re-running is always safe.

    Returns:
        A :class:`FolderCreationResult` detailing what was created / failed.
    """
    result = FolderCreationResult()
    for rel_path in relative_paths:
        full_path = os.path.join(root_path, rel_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            result.created.append(full_path)
        except Exception as e:
            result.errors.append((full_path, str(e)))
            print(f"[template_engine] Error creating '{full_path}': {e}")
    return result


# ── Tree Renderer ──────────────────────────────────────────────────────────────

def format_paths_as_tree(paths: list[str], root_dir: str) -> str:
    """
    Converts a flat list of relative paths into a human-readable ASCII tree.

    Example output::

        /root/
        ├── 00-BRIEFING/
        └── 10-OWN_FOOTAGE/
            └── 00-RENDER/

    Args:
        paths:    Flat list of relative directory paths.
        root_dir: Label shown at the top of the tree.

    Returns:
        A multi-line string ready to display in a text widget.
    """
    if not paths:
        return "(No folders to create)"

    # Build a nested dict representing the tree
    tree: dict = {}
    for path in paths:
        parts = path.split(os.sep)
        node = tree
        for part in parts:
            node = node.setdefault(part, {})

    def _render(node: dict, indent: str = "") -> str:
        lines = ""
        keys = list(node.keys())
        for i, key in enumerate(keys):
            connector = "└── " if i == len(keys) - 1 else "├── "
            lines += f"{indent}{connector}{key}/\n"
            child_indent = indent + ("    " if i == len(keys) - 1 else "│   ")
            lines += _render(node[key], child_indent)
        return lines

    return f"{root_dir}/\n" + _render(tree)
