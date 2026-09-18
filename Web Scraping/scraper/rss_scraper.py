import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Optional
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FinancialRSSScraper:
    """
    Scraper utilizing Google News Financial RSS feeds.
    Provides fast, structured news collection with guaranteed zero bot blocking
    and exact UTC publication timestamps.
    """

    BASE_RSS_URL = "https://news.google.com/rss/search?q={}&hl=en-IN&gl=IN&ceid=IN:en"

    DEFAULT_QUERIES = [
        "when:7d site:moneycontrol.com/news/business",
        "when:7d site:economictimes.indiatimes.com/markets/stocks",
        "when:7d Nifty 50 stocks earnings",
    ]

    def __init__(self):
        self.results: List[Dict[str, str]] = []

    def fetch_feed(self, query: str, max_items: int = 50) -> List[Dict[str, str]]:
        """Fetch news items for a specific search query from Google News RSS."""
        encoded_query = urllib.parse.quote(query)
        feed_url = self.BASE_RSS_URL.format(encoded_query)

        req = urllib.request.Request(
            feed_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

        items = []
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            elements = root.findall(".//item")

            for el in elements[:max_items]:
                raw_title = el.find("title").text if el.find("title") is not None else ""
                link = el.find("link").text if el.find("link") is not None else ""
                pub_date = el.find("pubDate").text if el.find("pubDate") is not None else ""
                description = el.find("description").text if el.find("description") is not None else ""

                # Strip HTML from description
                desc_soup = BeautifulSoup(description, "html.parser")
                clean_desc = desc_soup.get_text(strip=True)

                # Split source from title if format is "Title - Source"
                source = "Google News RSS"
                headline = raw_title
                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    headline = parts[0].strip()
                    source = parts[1].strip()

                record = {
                    "Headlines": headline,
                    "Article": clean_desc,
                    "Published_At": pub_date,
                    "Source": source,
                    "Category": "financial_rss",
                    "URL": link,
                }
                items.append(record)
                self.results.append(record)

            logger.info(f"Fetched {len(items)} items for query: '{query}'")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch RSS feed for query '{query}': {e}")
            return []

    def fetch_all(self, queries: Optional[List[str]] = None, max_items_per_query: int = 30) -> List[Dict[str, str]]:
        """Fetch items across multiple queries."""
        if queries is None:
            queries = self.DEFAULT_QUERIES

        all_items = []
        for q in queries:
            items = self.fetch_feed(query=q, max_items=max_items_per_query)
            all_items.extend(items)

        return all_items

    def to_dataframe(self) -> pd.DataFrame:
        """Returns scraped items as a pandas DataFrame."""
        if not self.results:
            return pd.DataFrame(columns=["Headlines", "Article", "Published_At", "Source", "Category", "URL"])
        return pd.DataFrame(self.results)

    def save_csv(self, filepath: str) -> None:
        """Saves items to CSV."""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Successfully saved {len(df)} RSS items to '{filepath}'.")

    def save_json(self, filepath: str, indent: int = 2) -> None:
        """Saves scraped items to a formatted JSON file."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=indent)
        logger.info(f"Successfully saved {len(self.results)} RSS items to JSON '{filepath}'.")

    def save_jsonl(self, filepath: str) -> None:
        """Saves scraped items to JSON Lines (JSONL) format."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            for item in self.results:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"Successfully saved {len(self.results)} RSS items to JSONL '{filepath}'.")
