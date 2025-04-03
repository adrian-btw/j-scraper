import os
import json
from typing import Any, Dict, Optional, Set


class FileStorageManager:
    """Manages loading and saving scraped data using unique IDs."""

    def __init__(self, data_dir: str = "data/scraped_data") -> None:
        """
        Initializes the storage manager.

        Args:
            data_dir (str): Directory where scraped data will be stored.
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # Track processed IDs
        self.processed_file = os.path.join(data_dir, "processed_ids.txt")
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> Set[str]:
        """
        Loads the set of processed IDs from file.

        Returns:
            Set[str]: A set of previously processed IDs.
        """
        if os.path.exists(self.processed_file):
            with open(self.processed_file, "r") as f:
                return set(line.strip() for line in f.readlines())
        return set()

    def is_processed(self, item_id: str) -> bool:
        """
        Checks if an ID has already been processed.

        Args:
            item_id (str): The unique identifier.

        Returns:
            bool: True if the ID has been processed, False otherwise.
        """
        return item_id in self.processed_ids

    def _mark_as_processed(self, item_id: str) -> None:
        """
        Marks an ID as processed by adding it to the processed file.

        Args:
            item_id (str): The unique identifier to mark as processed.
        """
        self.processed_ids.add(item_id)
        with open(self.processed_file, "a") as f:
            f.write(f"{item_id}\n")

    def save_data(self, item_id: str, data: Dict[str, Any]) -> str:
        """
        Saves scraped data associated with an ID.

        Args:
            item_id (str): The unique identifier.
            data (Dict[str, Any]): The scraped data to save.

        Returns:
            str: The file path where data was saved.
        """
        filepath = os.path.join(self.data_dir, f"{item_id}.json")

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        self._mark_as_processed(item_id)
        return filepath

    def get_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves scraped data for a given ID.

        Args:
            item_id (str): The unique identifier.

        Returns:
            Optional[Dict[str, Any]]: The retrieved data, or None if not found.
        """
        filepath = os.path.join(self.data_dir, f"{item_id}.json")

        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return None
