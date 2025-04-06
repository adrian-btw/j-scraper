import os
import json
from typing import Any, Dict, Optional, Set


class FileStorageManager:
    """Manages loading and saving scraped data using unique IDs."""

    def __init__(self, data_dir: str = "data/scraped_data") -> None:
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.processed_file = os.path.join(data_dir, "processed_ids.txt")
        self.errored_file = os.path.join(data_dir, "errored_ids.txt")

        self.processed_ids = self._load_ids(self.processed_file)
        self.errored_ids = self._load_ids(self.errored_file)

    def _load_ids(self, path: str) -> Set[str]:
        if os.path.exists(path):
            with open(path, "r") as f:
                return set(line.strip() for line in f.readlines())
        return set()

    def _save_ids(self, path: str, ids: Set[str]) -> None:
        with open(path, "w") as f:
            for item_id in sorted(ids):
                f.write(f"{item_id}\n")

    def is_processed(self, item_id: str) -> bool:
        return item_id in self.processed_ids

    def save_data(self, item_id: str, data: Dict[str, Any]) -> str:
        filepath = os.path.join(self.data_dir, f"{item_id}.json")

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        has_errors = bool(data.get("_metadata", {}).get("errors"))

        if has_errors:
            self.errored_ids.add(item_id)
            self._save_ids(self.errored_file, self.errored_ids)
        else:
            self.processed_ids.add(item_id)
            self._save_ids(self.processed_file, self.processed_ids)

            # If it was previously errored, remove it
            if item_id in self.errored_ids:
                self.errored_ids.remove(item_id)
                self._save_ids(self.errored_file, self.errored_ids)

        return filepath

    def get_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        filepath = os.path.join(self.data_dir, f"{item_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return None
