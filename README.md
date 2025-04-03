# Web Scraper

This project contains a web scraper that extracts data from webpages using unique IDs. The scraper reconstructs URLs from a common prefix and saves the scraped data in a structured format.

## Prerequisites

Ensure you have Python 3 installed along with the necessary dependencies:

```sh
pip install -r requirements.txt
```

## Running the Scraper

1. Prepare a text file (e.g., `ids.txt`) containing one unique ID per line:

```
12345
67890
abcdef
```

2. Determine the common URL prefix (e.g., `https://example.com/item/`).

3. Run the scraper with the following command:

```sh
python main.py --ids ids.txt --url_prefix "https://example.com/item/"
```

## Output

- Scraped data is saved in the `data/scraped_data/` directory as JSON files.
- A log of processed IDs is maintained to prevent duplicate scraping.

## Notes

- The scraper runs headlessly using Selenium.
- Ensure that the webpage structure aligns with the `_extract_data` method in `scraper.py`.
- You can interrupt the process safely with `Ctrl + C`, and progress will be saved.

## Troubleshooting

If you encounter issues, ensure:
- Chrome and ChromeDriver are installed and up to date.
- Required Python packages are installed.
- The URL prefix correctly maps to the item IDs.

For further customization, modify `_extract_data` in `scraper.py` to fit your scraping needs.

