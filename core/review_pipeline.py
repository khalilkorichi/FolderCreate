"""
core/review_pipeline.py
───────────────────────
Enhanced Review Pipeline Engine:
- Ultra-fast image header inspection using Pillow without full byte decoding.
- Automatic dimension recognition & social media layout tagging:
    • Instagram / Reel / TikTok Stories (9:16)
    • Instagram Portrait Posts / Ads (4:5 / 3:4)
    • Square Posts (1:1)
    • Facebook / Web Ad Banners (1.91:1)
    • Full HD / Presentation / YouTube (16:9)
    • Fallback vector and raw project tags (PSD, AI, PDF, SVG, etc.)
- Custom tag lookup and persistence synchronization via AppStore.
- Cut-and-paste file approval to `03_Approved` with tag transfer.
"""

import os
import shutil
from typing import Any, Dict, List, Optional
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def detect_design_info(filepath: str) -> Dict[str, Any]:
    """
    Reads image dimensions and infers the design format & smart tag.
    Takes <1ms because Pillow only reads file headers without decoding pixels.
    """
    _, ext = os.path.splitext(filepath)
    ext_lower = ext.lower()

    # Default fallback info
    info = {
        "is_image": False,
        "width": 0,
        "height": 0,
        "dimensions_str": "ملف مشروع",
        "aspect_ratio": None,
        "auto_tag": "ملف تصميم",
        "tag_type": "file",
        "tag_color": "#7F8C8D"
    }

    if ext_lower in IMAGE_EXTENSIONS:
        try:
            with Image.open(filepath) as img:
                w, h = img.size
                info["is_image"] = True
                info["width"] = w
                info["height"] = h
                info["dimensions_str"] = f"{w} × {h} px"

                ratio = round(w / h, 4) if h > 0 else 1.0
                info["aspect_ratio"] = ratio

                # 1. Instagram Story / Reels / Shorts (9:16 vertical)
                if (abs(w - 1080) <= 8 and abs(h - 1920) <= 8) or (0.54 <= ratio <= 0.58 and h > w):
                    info["auto_tag"] = "📱 ستوري / ريلز (9:16)"
                    info["tag_type"] = "story"
                    info["tag_color"] = "#8E44AD"

                # 2. Instagram Portrait / Social Ads (4:5 or 3:4 vertical)
                elif ((abs(w - 1080) <= 8 and h in (1350, 1440))
                      or (0.70 <= ratio <= 0.85 and h > w)):
                    info["auto_tag"] = "📸 منشور إنستغرام / إعلاني (4:5)"
                    info["tag_type"] = "portrait_post"
                    info["tag_color"] = "#E91E63"

                # 3. Square Post (1:1)
                elif 0.97 <= ratio <= 1.03:
                    info["auto_tag"] = "⏹️ منشور مربع (1:1)"
                    info["tag_type"] = "square"
                    info["tag_color"] = "#27AE60"

                # 4. Link Ad / Landscape Banner (1.91:1)
                elif (1.85 <= ratio <= 1.95 and w > h) or (w == 1200 and h in (628, 630)):
                    info["auto_tag"] = "🌐 غلاف / رابط إعلاني (1.91:1)"
                    info["tag_type"] = "ad_banner"
                    info["tag_color"] = "#2980B9"

                # 5. Full HD / YouTube / Screen (16:9)
                elif (1.70 <= ratio <= 1.82 and w > h) or (w == 1920 and h == 1080):
                    info["auto_tag"] = "🖥️ شاشة كاملة / يوتيوب (16:9)"
                    info["tag_type"] = "screen_16_9"
                    info["tag_color"] = "#D35400"

                # 6. General Landscape
                elif w > h:
                    info["auto_tag"] = f"🖼️ بانر / أفقي ({w}×{h})"
                    info["tag_type"] = "landscape"
                    info["tag_color"] = "#34495E"

                # 7. General Portrait
                else:
                    info["auto_tag"] = f"📐 تصميم طولي ({w}×{h})"
                    info["tag_type"] = "portrait"
                    info["tag_color"] = "#16A085"

                return info
        except Exception:
            # Corrupted or unreadable image header; proceed to fallback
            pass

    # Non-image or unreadable files categorized by extension
    ext_clean = ext_lower.replace(".", "").upper()
    if ext_lower == ".psd":
        info["auto_tag"] = "🎨 ملف فوتوشوب PSD"
        info["tag_type"] = "psd"
        info["tag_color"] = "#1F78D1"
    elif ext_lower == ".ai":
        info["auto_tag"] = "🖋️ ملف إليستريتور AI"
        info["tag_type"] = "ai"
        info["tag_color"] = "#E67E22"
    elif ext_lower in (".eps", ".svg"):
        info["auto_tag"] = f"✒️ فيكتور {ext_clean}"
        info["tag_type"] = "vector"
        info["tag_color"] = "#D68910"
    elif ext_lower == ".pdf":
        info["auto_tag"] = "📑 مستند PDF"
        info["tag_type"] = "pdf"
        info["tag_color"] = "#C0392B"
    elif ext_lower in (".indd", ".idml"):
        info["auto_tag"] = "📖 تصميم InDesign"
        info["tag_type"] = "indesign"
        info["tag_color"] = "#AF2B65"
    elif ext_lower in (".fig", ".xd"):
        info["auto_tag"] = f"📱 واجهات {ext_clean}"
        info["tag_type"] = "ui"
        info["tag_color"] = "#9B59B6"
    else:
        info["auto_tag"] = f"📁 ملف {ext_clean}" if ext_clean else "ملف غير معروف"

    return info


def scan_review_files(client_root: str, app_store: Optional[Any] = None) -> List[Dict[str, Any]]:
    """
    Finds all files pending review inside any `02_In_Review` folder across all years/months.
    Enriches each item with dimensions, auto-detected tag, and custom user tag.
    """
    review_items = []
    if not os.path.exists(client_root):
        return review_items

    for root, dirs, files in os.walk(client_root):
        if os.path.basename(root) == "02_In_Review":
            # Approved folder is located beside 02_In_Review
            parent_dir = os.path.dirname(root)
            approved_dir = os.path.join(parent_dir, "03_Approved")
            month_name = os.path.basename(parent_dir)
            year_name = os.path.basename(os.path.dirname(parent_dir))

            for f in files:
                file_path = os.path.join(root, f)
                try:
                    size_bytes = os.path.getsize(file_path)
                    size_kb = round(size_bytes / 1024, 1)
                    if size_kb >= 1024:
                        size_display = f"{size_kb / 1024:.2f} MB"
                    else:
                        size_display = f"{size_kb} KB"
                except OSError:
                    size_kb = 0
                    size_display = "0 KB"

                # Extract design dimensions & auto-tags
                d_info = detect_design_info(file_path)

                # Check custom user tag override
                custom_tag = app_store.get_design_tag(file_path) if app_store else None
                if custom_tag:
                    effective_tag = f"🏷️ {custom_tag}"
                    is_custom_tagged = True
                    tag_color = "#F39C12"  # Gold accent for user-customized tags
                else:
                    effective_tag = d_info["auto_tag"]
                    is_custom_tagged = False
                    tag_color = d_info["tag_color"]

                review_items.append({
                    "filename": f,
                    "filepath": file_path,
                    "size_kb": size_kb,
                    "size_display": size_display,
                    "month": month_name,
                    "year": year_name,
                    "approved_dir": approved_dir,
                    "is_image": d_info["is_image"],
                    "width": d_info["width"],
                    "height": d_info["height"],
                    "dimensions_str": d_info["dimensions_str"],
                    "auto_tag": d_info["auto_tag"],
                    "effective_tag": effective_tag,
                    "raw_tag": custom_tag or d_info["auto_tag"],
                    "is_custom_tagged": is_custom_tagged,
                    "tag_color": tag_color
                })

    return review_items


def approve_file(source_filepath: str, target_approved_dir: str, app_store: Optional[Any] = None) -> bool:
    """
    Moves (cut & paste) a design file from `02_In_Review` to `03_Approved`.
    Safely transfers any assigned custom tag to the new path.
    """
    if not os.path.exists(source_filepath):
        return False

    try:
        os.makedirs(target_approved_dir, exist_ok=True)
        filename = os.path.basename(source_filepath)
        dest_filepath = os.path.join(target_approved_dir, filename)

        # Handle name collision by appending counter
        if os.path.exists(dest_filepath):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_filepath):
                dest_filepath = os.path.join(target_approved_dir, f"{base}_{counter}{ext}")
                counter += 1

        shutil.move(source_filepath, dest_filepath)

        # Transfer custom tag to new destination if exists
        if app_store:
            app_store.transfer_design_tag(source_filepath, dest_filepath)

        return True
    except Exception as e:
        print(f"[review_pipeline] Error approving file {source_filepath}: {e}")
        return False
