"""
core/client_manager.py
──────────────────────
Provides business logic for creating client folder hierarchies:
- Standard Brand Assets (_Brand_Assets)
- Zero-padded Year / Month structures
- Subfolders for Resources, PSDs, In_Review, Approved, and _TEMP
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple


MONTH_NAMES = [
    (1, "01_January"),
    (2, "02_February"),
    (3, "03_March"),
    (4, "04_April"),
    (5, "05_May"),
    (6, "06_June"),
    (7, "07_July"),
    (8, "08_August"),
    (9, "09_September"),
    (10, "10_October"),
    (11, "11_November"),
    (12, "12_December"),
]

BRAND_ASSET_SUBFOLDERS = [
    "01_Logos",
    "02_Fonts",
    "03_Colors_Guidelines",
    "04_Mockups_References",
]

MONTH_WORKFLOW_SUBFOLDERS = [
    "00_Resources",
    "01_Sources_PSD",
    "02_In_Review",
    "03_Approved",
    "_TEMP",
]


def init_client_brand_assets(client_root: str) -> List[str]:
    """
    Creates standard _Brand_Assets folders inside the client directory.
    Returns list of paths created.
    """
    created = []
    base_brand = os.path.join(client_root, "_Brand_Assets")
    for sub in BRAND_ASSET_SUBFOLDERS:
        path = os.path.join(base_brand, sub)
        os.makedirs(path, exist_ok=True)
        created.append(path)
    return created


def create_month_structure(
    client_root: str,
    year: int = None,
    month: int = None,
    custom_subfolders: List[str] = None
) -> Tuple[str, List[str]]:
    """
    Creates standard structured monthly directory for a client:
    Format: [client_root]/[YYYY]/[MM_MonthName]/[00_Resources, 01_Sources_PSD, ...]

    Returns:
        (month_dir_path, list_of_subfolder_paths)
    """
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    # Get standard zero-padded month name
    month_folder_name = next((name for m_num, name in MONTH_NAMES if m_num == month), f"{month:02d}_Month")

    month_dir = os.path.join(client_root, str(year), month_folder_name)
    os.makedirs(month_dir, exist_ok=True)

    subfolders = custom_subfolders if custom_subfolders is not None else MONTH_WORKFLOW_SUBFOLDERS
    created = []
    for sub in subfolders:
        sub_path = os.path.join(month_dir, sub)
        os.makedirs(sub_path, exist_ok=True)
        created.append(sub_path)

    return month_dir, created


def get_existing_client_years(client_root: str) -> List[str]:
    """Returns list of existing year folders (4 digits) in client directory."""
    if not os.path.exists(client_root):
        return []
    years = []
    for item in os.listdir(client_root):
        if item.isdigit() and len(item) == 4 and os.path.isdir(os.path.join(client_root, item)):
            years.append(item)
    return sorted(years, reverse=True)


def get_existing_months_for_year(client_root: str, year: str) -> List[str]:
    """Returns list of existing month folders in client's year directory."""
    year_dir = os.path.join(client_root, str(year))
    if not os.path.exists(year_dir):
        return []
    months = []
    for item in os.listdir(year_dir):
        if os.path.isdir(os.path.join(year_dir, item)):
            months.append(item)
    return sorted(months)
