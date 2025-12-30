import argparse
import config
import json
from pathlib import Path
from typing import List, Optional
from scraper.scraper import WebScraper
from scraper.file_storage import FileStorageManager


def load_ids_from_file(file_path: str, access_key: Optional[str] = None) -> List[str]:
    """
    Loads a list of unique IDs from a file.
    Supports both text files (one ID per line) and JSON files.

    Args:
        file_path (str): Path to the file containing IDs.
        access_key (str, optional): For JSON files, dot-separated path to the list
            (e.g., "game_ids" or "foo.bar.baz"). Required for JSON files.

    Returns:
        List[str]: A list of IDs as strings.

    Raises:
        ValueError: If JSON file is provided without access_key, or if access_key
            doesn't point to a list in the JSON.
    """
    file_path_obj = Path(file_path)
    file_extension = file_path_obj.suffix.lower()

    if file_extension == ".json":
        if access_key is None:
            raise ValueError(
                "access_key is required for JSON files. "
                "Provide it using --access-key argument."
            )

        with open(file_path, "r") as f:
            data = json.load(f)

        # Navigate through the JSON using the access key path
        keys = access_key.split(".")
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                raise ValueError(
                    f"Access key path '{access_key}' not found in JSON file. "
                    f"Failed at key '{key}'."
                )
            current = current[key]

        # Ensure we have a list
        if not isinstance(current, list):
            raise ValueError(
                f"Access key path '{access_key}' does not point to a list. "
                f"Found type: {type(current).__name__}"
            )

        # Convert all items to strings
        return [str(item) for item in current]

    else:
        # Treat as text file (one ID per line)
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]


def main() -> None:
    """
    Main function to run the web scraper with ID-based input.
    """
    arg_parser = argparse.ArgumentParser(description="Web Scraper")
    arg_parser.add_argument(
        "--ids", required=True, help="Path to file containing IDs to scrape"
    )
    arg_parser.add_argument(
        "--parser",
        required=True,
        choices=["jeopardy_game", "jeopardy_season_list"],
        help="Parser to use (jeopardy_game, jeopardy_season_list)",
    )
    arg_parser.add_argument(
        "--access-key",
        help="For JSON files, dot-separated path to the list (e.g., 'game_ids'). "
        "Required when --ids points to a JSON file.",
    )

    args = arg_parser.parse_args()

    storage = FileStorageManager(data_dir=f"{config.DATA_DIR}/{args.parser}")
    scraper = WebScraper(storage_manager=storage, parser=args.parser)

    try:
        item_ids = load_ids_from_file(args.ids, access_key=args.access_key)
        scraper.scrape_multiple(item_ids)

    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
