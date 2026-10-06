"""
data/client_store.py
────────────────────
Handles persistence and querying for clients and active workspaces.
Uses JSON storage in `data/clients.json`.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")


class ClientStore:
    def __init__(self, filepath: str = CLIENTS_FILE):
        self.filepath = filepath
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({"clients": []}, f, indent=4, ensure_ascii=False)

    def load_clients(self) -> List[Dict[str, Any]]:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("clients", [])
        except Exception as e:
            print(f"[client_store] Error loading clients: {e}")
            return []

    def save_clients(self, clients: List[Dict[str, Any]]) -> bool:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({"clients": clients}, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[client_store] Error saving clients: {e}")
            return False

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        clients = self.load_clients()
        for c in clients:
            if c.get("id") == client_id:
                return c
        return None

    def add_client(self, name: str, code: str, root_path: str, logo_path: str = "") -> Dict[str, Any]:
        clients = self.load_clients()
        new_client = {
            "id": str(uuid.uuid4())[:8],
            "name": name.strip(),
            "code": code.strip().upper(),
            "root_path": root_path.strip(),
            "logo_path": logo_path.strip(),
            "is_favorite": False,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
        }
        clients.append(new_client)
        self.save_clients(clients)
        return new_client

    def update_client(self, client_id: str, updates: Dict[str, Any]) -> bool:
        clients = self.load_clients()
        updated = False
        for c in clients:
            if c.get("id") == client_id:
                c.update(updates)
                updated = True
                break
        if updated:
            return self.save_clients(clients)
        return False

    def delete_client(self, client_id: str) -> bool:
        clients = self.load_clients()
        filtered = [c for c in clients if c.get("id") != client_id]
        if len(filtered) != len(clients):
            return self.save_clients(filtered)
        return False

    def toggle_favorite(self, client_id: str) -> bool:
        clients = self.load_clients()
        for c in clients:
            if c.get("id") == client_id:
                c["is_favorite"] = not c.get("is_favorite", False)
                self.save_clients(clients)
                return c["is_favorite"]
        return False

    def touch_client(self, client_id: str) -> None:
        """Update last accessed timestamp."""
        self.update_client(client_id, {"last_accessed": datetime.now().isoformat()})
