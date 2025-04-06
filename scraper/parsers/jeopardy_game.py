import re
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
)


class JeopardyGameParser:
    """Parses Jeopardy! game data from a Selenium-loaded page."""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def parse(self) -> dict:
        """Extracts structured data from a Jeopardy! game page."""
        data = {
            "game_id": None,
            "game_date": None,
            "clues": [],
            "skipped_clues": [],
            "_metadata": {"errors": []},
        }

        try:
            data["game_id"], data["game_date"] = self._extract_game_metadata()
            if data["game_id"] is None or data["game_date"] is None:
                data["_metadata"]["errors"].append("Missing game metadata.")

            for round_id, round_name in {
                "jeopardy_round": "SJ",
                "double_jeopardy_round": "DJ",
            }.items():
                self._extract_main_round_data(round_id, round_name, data)

            self._extract_final_round_data(data)

        except Exception as e:
            data["_metadata"]["errors"].append(f"Unhandled exception in parse: {e}")

        return data

    def _extract_game_metadata(self) -> tuple[int | None, str | None]:
        try:
            game_title = self.driver.find_element(By.ID, "game_title").text
            match = re.search(r"Show #(\d+) - (.+)", game_title)
            if match:
                return int(match.group(1)), match.group(2).strip()
        except Exception:
            pass
        return None, None

    def _extract_main_round_data(
        self, round_id: str, round_name: str, data: dict
    ) -> None:
        try:
            round_element = self.driver.find_element(By.ID, round_id)
            categories = self._extract_categories(round_element)

            clue_elements = round_element.find_elements(By.CLASS_NAME, "clue")
            for clue_index, clue_element in enumerate(clue_elements):
                try:
                    clue_text = clue_element.find_element(
                        By.CLASS_NAME, "clue_text"
                    ).text.strip()
                    is_daily_double = self._is_daily_double(clue_element)
                    dollar_val = self._infer_dollar_value(clue_index, round_name)

                    self._click_clue_value(clue_element)
                    correct_response = self._extract_correct_response(clue_element)

                    category_index = clue_index % len(categories)
                    category = (
                        categories[category_index]
                        if category_index < len(categories)
                        else "Unknown"
                    )

                    data["clues"].append(
                        {
                            "category": category,
                            "clue_text": clue_text,
                            "correct_response": correct_response,
                            "round": round_name,
                            "is_daily_double": is_daily_double,
                            "dollar_val": dollar_val,
                        }
                    )

                except Exception as clue_error:
                    data["skipped_clues"].append(
                        {
                            "round": round_name,
                            "error": str(clue_error),
                            "raw_html": clue_element.get_attribute("outerHTML"),
                        }
                    )

        except Exception as e:
            data["_metadata"]["errors"].append(
                f"Failed to extract round {round_name}: {e}"
            )

    def _extract_final_round_data(self, data: dict) -> None:
        try:
            final_round = self.driver.find_element(By.ID, "final_jeopardy_round")
            category = final_round.find_element(
                By.CLASS_NAME, "category_name"
            ).text.strip()
            clue_text = final_round.find_element(
                By.CLASS_NAME, "clue_text"
            ).text.strip()

            category_row = final_round.find_element(By.TAG_NAME, "tr")
            category_row.click()

            correct_response = final_round.find_element(
                By.CLASS_NAME, "correct_response"
            ).text.strip()

            data["clues"].append(
                {
                    "category": category,
                    "clue_text": clue_text,
                    "correct_response": correct_response,
                    "round": "FJ",
                    "is_daily_double": False,
                    "dollar_val": None,
                }
            )

        except Exception as e:
            data["_metadata"]["errors"].append(f"Failed to extract Final Jeopardy: {e}")

    def _extract_categories(self, round_element) -> list[str]:
        return [
            cat.text.strip()
            for cat in round_element.find_elements(By.CLASS_NAME, "category_name")
        ]

    def _is_daily_double(self, clue_element) -> bool:
        try:
            clue_element.find_element(By.CLASS_NAME, "clue_value_daily_double")
            return True
        except NoSuchElementException:
            return False

    def _click_clue_value(self, clue_element) -> None:
        try:
            try:
                value_element = clue_element.find_element(By.CLASS_NAME, "clue_value")
            except NoSuchElementException:
                value_element = clue_element.find_element(
                    By.CLASS_NAME, "clue_value_daily_double"
                )
            value_element.click()
        except (NoSuchElementException, ElementClickInterceptedException):
            pass

    def _extract_correct_response(self, clue_element) -> str:
        try:
            return clue_element.find_element(
                By.CLASS_NAME, "correct_response"
            ).text.strip()
        except NoSuchElementException:
            return "[Unknown]"

    def _infer_dollar_value(self, clue_index: int, round_name: str) -> int:
        row = clue_index // 6
        if round_name == "SJ":
            return [200, 400, 600, 800, 1000][row]
        elif round_name == "DJ":
            return [400, 800, 1200, 1600, 2000][row]
        return None
