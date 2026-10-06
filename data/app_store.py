"""
data/app_store.py
─────────────────
Unified persistence engine for:
- Clients (list, metadata, logos)
- Favorites (pinned files and folders)
- Recents (tracking accessed/created directories with timestamps)
- Temp folders cache
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DATA_DIR, "app_data.json")


class AppStore:
    def __init__(self, filepath: str = DB_FILE):
        self.filepath = filepath
        self._cache: Optional[Dict[str, Any]] = None
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(self.filepath):
            initial_data = {
                "clients": [],
                "favorites": [],
                "recents": [],
                "design_tags": {}
            }
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)
            self._cache = initial_data

    def _read_data(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
                return self._cache
        except Exception as e:
            print(f"[app_store] Error reading data: {e}")
            self._cache = {"clients": [], "favorites": [], "recents": [], "design_tags": {}}
            return self._cache

    def _write_data(self, data: Dict[str, Any]) -> bool:
        self._cache = data
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[app_store] Error writing data: {e}")
            return False

    def invalidate_cache(self) -> None:
        self._cache = None

    # ── Clients ─────────────────────────────────────────────────────────────
    def get_clients(self) -> List[Dict[str, Any]]:
        return self._read_data().get("clients", [])

    def add_client(self, name: str, code: str, root_path: str, logo_path: str = "") -> Dict[str, Any]:
        data = self._read_data()
        client = {
            "id": str(uuid.uuid4())[:8],
            "name": name.strip(),
            "code": code.strip().upper(),
            "root_path": root_path.strip(),
            "logo_path": logo_path.strip(),
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        data.setdefault("clients", []).append(client)
        self._write_data(data)
        self.add_recent("client", name, root_path)
        return client

    def delete_client(self, client_id: str) -> bool:
        data = self._read_data()
        clients = [c for c in data.get("clients", []) if c.get("id") != client_id]
        data["clients"] = clients
        return self._write_data(data)

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        for c in self.get_clients():
            if c.get("id") == client_id:
                return c
        return None

    # ── Favorites ───────────────────────────────────────────────────────────
    def get_favorites(self) -> List[Dict[str, Any]]:
        return self._read_data().get("favorites", [])

    def add_favorite(self, title: str, path: str, item_type: str = "folder", client_name: str = "") -> Dict[str, Any]:
        data = self._read_data()
        favs = data.get("favorites", [])
        # Avoid duplicate paths
        for fav in favs:
            if fav.get("path") == path:
                return fav

        new_fav = {
            "id": str(uuid.uuid4())[:8],
            "title": title.strip() or os.path.basename(path),
            "path": path.strip(),
            "type": item_type,  # 'folder' or 'file'
            "client_name": client_name.strip(),
            "added_at": datetime.now().isoformat()
        }
        favs.append(new_fav)
        data["favorites"] = favs
        self._write_data(data)
        return new_fav

    def remove_favorite(self, fav_id: str) -> bool:
        data = self._read_data()
        data["favorites"] = [f for f in data.get("favorites", []) if f.get("id") != fav_id]
        return self._write_data(data)

    # ── Recents ─────────────────────────────────────────────────────────────
    def get_recents(self, limit: int = 30) -> List[Dict[str, Any]]:
        recents = self._read_data().get("recents", [])
        return sorted(recents, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def add_recent(self, item_type: str, title: str, path: str) -> None:
        data = self._read_data()
        recents = data.get("recents", [])
        # Remove existing instance of same path to bring it to top
        recents = [r for r in recents if r.get("path") != path]
        recents.insert(0, {
            "type": item_type,  # 'folder', 'file', 'client', 'month'
            "title": title,
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        data["recents"] = recents[:50]  # Cap at 50
        self._write_data(data)

    # ── Design Tags ────────────────────────────────────────────────────────
    def get_design_tag(self, filepath: str) -> Optional[str]:
        if not filepath:
            return None
        norm_key = os.path.normcase(os.path.normpath(filepath))
        tags = self._read_data().get("design_tags", {})
        return tags.get(norm_key)

    def set_design_tag(self, filepath: str, tag: str) -> None:
        if not filepath:
            return
        data = self._read_data()
        tags = data.setdefault("design_tags", {})
        norm_key = os.path.normcase(os.path.normpath(filepath))
        if tag.strip():
            tags[norm_key] = tag.strip()
        else:
            tags.pop(norm_key, None)
        self._write_data(data)

    def remove_design_tag(self, filepath: str) -> bool:
        if not filepath:
            return False
        data = self._read_data()
        tags = data.get("design_tags", {})
        norm_key = os.path.normcase(os.path.normpath(filepath))
        if norm_key in tags:
            del tags[norm_key]
            return self._write_data(data)
        return False

    def transfer_design_tag(self, old_filepath: str, new_filepath: str) -> None:
        if not old_filepath or not new_filepath:
            return
        old_key = os.path.normcase(os.path.normpath(old_filepath))
        new_key = os.path.normcase(os.path.normpath(new_filepath))
        data = self._read_data()
        tags = data.setdefault("design_tags", {})
        if old_key in tags:
            tag_val = tags.pop(old_key)
            tags[new_key] = tag_val
            self._write_data(data)

