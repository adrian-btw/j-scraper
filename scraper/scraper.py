import time
import config
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from scraper.parsers import JeopardyGameParser, JeopardySeasonListParser
import config


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

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
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

            # Extract data using JeopardyGameParser
            data = self.parser.parse()

            # Add metadata
            data["_metadata"] = {
                **data["_metadata"],
                "id": item_id,
                "url": url,
                "timestamp": datetime.now().isoformat(),
            }

            # Save the data
            self.storage.save_data(item_id, data)

            print(f"Successfully scraped {item_id}")
            return data

        except Exception as e:
            print(f"Error scraping {item_id}: {str(e)}")
            return None

    def scrape_multiple(self, item_ids: list[str]) -> list[dict]:
        """
        Scrapes multiple pages based on their unique IDs.

        Args:
            item_ids (list[str]): List of unique identifiers.

        Returns:
            list[dict]: List of extracted data.
        """
        results = []
        for item_id in item_ids:
            result = self.scrape_page(item_id)
            if result:
                results.append(result)
        return results

    def close(self) -> None:
        """Closes the Selenium WebDriver."""
        if hasattr(self, "driver"):
            self.driver.quit()
