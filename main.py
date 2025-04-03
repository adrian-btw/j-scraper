import argparse
import config
from typing import List
from scraper.scraper import WebScraper
from scraper.file_storage import FileStorageManager


def load_ids_from_file(file_path: str) -> List[str]:
    """
    Loads a list of unique IDs from a file.

    Args:
        file_path (str): Path to the file containing IDs.

    Returns:
        List[str]: A list of IDs.
    """
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

    args = arg_parser.parse_args()

    storage = FileStorageManager(data_dir=f"{config.DATA_DIR}/{args.parser}")
    scraper = WebScraper(storage_manager=storage, parser=args.parser)

    try:
        item_ids = load_ids_from_file(args.ids)
        scraper.scrape_multiple(item_ids)

    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
