from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


class JeopardySeasonListParser:
    """Placeholder parser for Jeopardy season list. Implementation coming soon."""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def parse(self) -> dict:
        """Extracts structured data from a Jeopardy! season list page."""
        data = {"game_ids": []}

        try:
            data["game_ids"] = self._extract_game_ids()

        except Exception as e:
            print(f"Failed to extract season list data: {e}")

        return data

    def _extract_game_ids(self) -> list[int]:
        content_element = self.driver.find_element(By.ID, "content")
        game_table_element = content_element.find_element(By.TAG_NAME, "table")
        game_row_elements = game_table_element.find_elements(By.TAG_NAME, "tr")
        game_links = [
            row_element.find_element(By.TAG_NAME, "a")
            for row_element in game_row_elements
        ]

        game_ids = [
            int(link.get_attribute("href").split("?game_id=")[-1])
            for link in game_links
        ]

        return game_ids
