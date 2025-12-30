import time
import config
import os
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from scraper.parsers import JeopardyGameParser, JeopardySeasonListParser


class WebScraper:
    """A web scraper that uses Selenium to extract data and stores it using FileStorageManager."""

    SUPPORTED_PARSERS = {
        "jeopardy_game": JeopardyGameParser,
        "jeopardy_season_list": JeopardySeasonListParser,
    }

    def __init__(
        self, storage_manager, parser: str, url_prefix: str = config.URL_PREFIX
    ) -> None:
        """
        Initializes the scraper with a storage manager, parser type, and URL prefix.

        Args:
            storage_manager: The storage manager responsible for saving and loading data.
            parser (str): The name of the parser to use.
            url_prefix (str): The common URL prefix to reconstruct full URLs from IDs.
        """
        if parser not in self.SUPPORTED_PARSERS:
            raise ValueError(
                f"Unsupported parser '{parser}'. Supported values: {list(self.SUPPORTED_PARSERS.keys())}"
            )

        self._setup_driver()

        self.storage = storage_manager
        self.url_prefix = url_prefix
        self.parser = self.SUPPORTED_PARSERS[parser](
            self.driver
        )  # Dynamically instantiate parser

    def _setup_driver(self) -> None:
        """Configures and initializes the Chrome WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Get the path from ChromeDriverManager and ensure we use the actual chromedriver executable
        driver_path = ChromeDriverManager().install()
        
        # Fix: ChromeDriverManager sometimes returns the wrong file (e.g., THIRD_PARTY_NOTICES.chromedriver)
        # We need to find the actual chromedriver executable
        driver_path_obj = Path(driver_path)
        
        # If the returned path doesn't point to the actual chromedriver executable
        if not driver_path_obj.name == 'chromedriver' or 'THIRD_PARTY' in driver_path or 'LICENSE' in driver_path:
            # Look for chromedriver in the same directory
            driver_dir = driver_path_obj.parent
            actual_chromedriver = driver_dir / 'chromedriver'
            
            if actual_chromedriver.exists() and actual_chromedriver.is_file():
                driver_path = str(actual_chromedriver)
            else:
                # Search in subdirectories (sometimes it's in a nested folder)
                for potential_driver in driver_dir.rglob('chromedriver'):
                    if (potential_driver.is_file() and 
                        potential_driver.name == 'chromedriver' and
                        'THIRD_PARTY' not in str(potential_driver) and
                        'LICENSE' not in str(potential_driver)):
                        # Ensure it's executable
                        os.chmod(potential_driver, 0o755)
                        driver_path = str(potential_driver)
                        break
        
        # Ensure the chromedriver is executable
        if os.path.exists(driver_path):
            os.chmod(driver_path, 0o755)

        self.driver = webdriver.Chrome(
            service=Service(driver_path), options=chrome_options
        )

    def scrape_page(self, item_id: str) -> dict | None:
        """
        Scrapes a webpage based on its unique ID.

        Args:
            item_id (str): The unique identifier for the page.

        Returns:
            dict | None: Extracted data if successful, otherwise None.
        """
        if self.storage.is_processed(item_id):
            print(f"Skipping {item_id} - already processed")
            return None

        url = f"{self.url_prefix}{item_id}"

        try:
            print(f"Scraping {url}")
            self.driver.get(url)

            # Delay to ensure the page loads
            time.sleep(2)

            # Extract data using parser
            data = self.parser.parse()

            # Add metadata
            existing_metadata = data.get("_metadata", {})
            data["_metadata"] = {
                **existing_metadata,
                "id": item_id,
                "url": url,
                "timestamp": datetime.now().isoformat(),
            }

            # Save the data (even if it has errors - partial data is better than nothing)
            self.storage.save_data(item_id, data)

            # Check if there were any errors
            errors = existing_metadata.get("errors", [])
            if errors:
                print(f"Scraped {item_id} with {len(errors)} error(s) - check metadata")
            else:
                print(f"Successfully scraped {item_id}")
            
            return data

        except Exception as e:
            # Save partial data with error information even if parsing completely fails
            error_message = f"Fatal error during scraping: {str(e)}"
            print(f"Error scraping {item_id}: {error_message}")
            
            # Create minimal data structure with error metadata
            error_data = {
                "_metadata": {
                    "errors": [error_message],
                    "id": item_id,
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "scrape_failed": True,
                }
            }
            
            # Try to save the error data
            try:
                self.storage.save_data(item_id, error_data)
                print(f"Saved error metadata for {item_id}")
            except Exception as save_error:
                print(f"Failed to save error metadata for {item_id}: {save_error}")
            
            return None

    def scrape_multiple(self, item_ids: list[str], limit: int | None = None) -> list[dict]:
        """
        Scrapes multiple pages based on their unique IDs.
        Stops on the first failed game, if any clues are skipped, or after reaching the limit.

        Args:
            item_ids (list[str]): List of unique identifiers.
            limit (int, optional): Maximum number of items to scrape. Stops after this many successful scrapes.

        Returns:
            list[dict]: List of extracted data.

        Raises:
            RuntimeError: If a game fails to scrape, has skipped clues, or other errors (stops iteration).
        """
        results = []
        for item_id in item_ids:
            # Check if we've reached the limit
            if limit is not None and len(results) >= limit:
                print(f"Reached limit of {limit} items. Stopping.")
                break
            
            result = self.scrape_page(item_id)
            if result is None:
                raise RuntimeError(
                    f"Scraping stopped: failed to scrape game {item_id}. "
                    f"Progress saved for {len(results)} game(s)."
                )
            
            # Check if the scrape was marked as failed
            if result.get("_metadata", {}).get("scrape_failed", False):
                raise RuntimeError(
                    f"Scraping stopped: game {item_id} failed. "
                    f"Progress saved for {len(results)} game(s)."
                )
            
            # Check if any clues were skipped (individual clue parsing errors)
            skipped_clues = result.get("skipped_clues", [])
            if len(skipped_clues) > 0:
                raise RuntimeError(
                    f"Scraping stopped: game {item_id} had {len(skipped_clues)} skipped clue(s). "
                    f"Progress saved for {len(results)} game(s)."
                )
            
            results.append(result)
        return results

    def close(self) -> None:
        """Closes the Selenium WebDriver."""
        if hasattr(self, "driver"):
            self.driver.quit()
