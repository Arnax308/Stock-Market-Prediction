import time
import random
import logging
import subprocess
from typing import List, Dict, Optional, Set
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class MoneycontrolScraper:
    """
    Robust scraper for Moneycontrol financial news articles.
    Extracts structured data: Headline, Article, Published_At, Source, Category, and URL.
    """

    CATEGORIES = {
        "companies": "https://www.moneycontrol.com/news/business/companies/page-{}/",
        "stocks": "https://www.moneycontrol.com/news/business/stocks/page-{}/",
        "markets": "https://www.moneycontrol.com/news/business/markets/page-{}/",
        "earnings": "https://www.moneycontrol.com/news/business/earnings/page-{}/",
        "economy": "https://www.moneycontrol.com/news/business/economy/page-{}/",
    }

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.moneycontrol.com/",
    }

    DISCLAIMER_KEYWORDS = [
        "disclaimer:",
        "first published:",
        "telegram channel",
        "whatsapp channel",
        "views and investment tips expressed",
        "moneycontrol.com advises users to check",
        "follow our live blog",
        "read also:",
    ]

    def __init__(self, delay_range: tuple = (0.5, 1.2), timeout: int = 15):
        self.delay_range = delay_range
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        
        # Configure robust retry strategy
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.seen_urls: Set[str] = set()
        self.articles_data: List[Dict[str, str]] = []

    def _sleep(self):
        time.sleep(random.uniform(*self.delay_range))

    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch URL with requests session, falling back to curl on connection/timeout errors."""
        try:
            res = self.session.get(url, timeout=self.timeout)
            if res.status_code == 200:
                return res.text
            logger.warning(f"HTTP {res.status_code} for {url}")
        except Exception as e:
            logger.debug(f"Requests error on {url} ({e}). Falling back to curl...")

        # Bulletproof fallback to native curl.exe (handles Windows TLS/IPv6 handshake tarpits)
        try:
            proc = subprocess.run(
                [
                    "curl.exe", "-s", "-L", "--max-time", str(self.timeout),
                    "-A", self.DEFAULT_HEADERS["User-Agent"],
                    url
                ],
                capture_output=True,
                timeout=self.timeout + 2,
            )
            if proc.returncode == 0 and len(proc.stdout) > 500:
                return proc.stdout.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Curl fallback failed for {url}: {e}")

        return None

    def _clean_paragraph(self, text: str) -> Optional[str]:
        text = text.strip()
        if len(text) < 25:
            return None
        lower = text.lower()
        for kw in self.DISCLAIMER_KEYWORDS:
            if kw in lower:
                return None
        return text

    def fetch_listing_urls(self, category: str, page: int) -> List[Dict[str, str]]:
        """Fetch news item links from a category listing page."""
        if category not in self.CATEGORIES:
            raise ValueError(f"Unknown category: {category}. Choose from: {list(self.CATEGORIES.keys())}")

        url = self.CATEGORIES[category].format(page)
        try:
            html = self._fetch_html(url)
            if not html:
                logger.warning(f"Failed to fetch listing {url}")
                return []

            soup = BeautifulSoup(html, "html.parser")
            items = []

            # Locate article list container
            cagetory_ul = soup.select_one("ul#cagetory")
            if not cagetory_ul:
                # Fallback selector for category list
                cagetory_ul = soup.select_one("ul.fleft, #left ul")

            if not cagetory_ul:
                logger.warning(f"Could not find category list container on {url}")
                return []

            for li in cagetory_ul.find_all("li", recursive=False):
                # Filter out promo cards or ads
                if "promos" in str(li) or "ad" in str(li.get("class", "")).lower():
                    continue

                h2 = li.find(["h2", "a"])
                if not h2:
                    continue

                a_tag = h2 if h2.name == "a" else h2.find("a")
                if not a_tag or not a_tag.get("href"):
                    continue

                article_url = a_tag["href"].strip()

                # Filter out promotional, audio, or video links
                if (
                    "moneycontrol.com/promos/" in article_url
                    or "/video/" in article_url
                    or "/podcast/" in article_url
                    or not article_url.startswith("http")
                ):
                    continue

                listing_title = a_tag.get_text(strip=True)
                if not listing_title or listing_title.lower() == "remove ad":
                    continue

                snippet_p = li.find("p")
                snippet = snippet_p.get_text(strip=True) if snippet_p else ""

                items.append({
                    "title": listing_title,
                    "url": article_url,
                    "category": category,
                    "snippet": snippet,
                })

            return items

        except Exception as e:
            logger.error(f"Error reading listing {url}: {e}")
            return []

    def fetch_article_detail(self, item: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Fetch and parse article details from an individual article page."""
        url = item["url"]
        if url in self.seen_urls:
            return None

        try:
            html = self._fetch_html(url)
            if not html:
                logger.warning(f"Failed to fetch article {url}")
                return None

            soup = BeautifulSoup(html, "html.parser")

            # Extract headline (prefer h1 on article page, fallback to listing title)
            h1 = soup.find("h1")
            headline = h1.get_text(strip=True) if h1 else item["title"]

            # Extract publication timestamp
            published_at = ""
            date_tag = soup.select_one(".article_schedule, .publish_date, .art-date, .article_author span")
            if date_tag:
                published_at = date_tag.get_text(strip=True)
            else:
                meta_time = soup.find("meta", property="article:published_time")
                if meta_time and meta_time.get("content"):
                    published_at = meta_time["content"]

            # Extract article body using multiple robust selector fallbacks
            content_div = soup.select_one("div#contentdata, div.arti-flow, div.content_wrapper")
            paragraphs = []

            if content_div:
                for p in content_div.find_all("p"):
                    cleaned = self._clean_paragraph(p.get_text())
                    if cleaned:
                        paragraphs.append(cleaned)

            # Fallback if content_div didn't yield paragraphs
            if not paragraphs:
                for p in soup.select("div#contentdata p, div.arti-flow p, div.content_wrapper p, div.article_content p"):
                    cleaned = self._clean_paragraph(p.get_text())
                    if cleaned:
                        paragraphs.append(cleaned)

            article_text = " ".join(paragraphs)
            if len(article_text) < 60:
                # If body is still empty, use listing snippet or meta description if available
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content") and len(meta_desc["content"]) > 50:
                    article_text = meta_desc["content"].strip()
                elif item.get("snippet") and len(item["snippet"]) > 50:
                    article_text = item["snippet"].strip()
                else:
                    logger.debug(f"Article text too short ({len(article_text)} chars) for {url}")
                    return None

            self.seen_urls.add(url)

            return {
                "Headlines": headline,
                "Article": article_text,
                "Published_At": published_at,
                "Source": "Moneycontrol",
                "Category": item["category"],
                "URL": url,
            }

        except Exception as e:
            logger.error(f"Error fetching article detail for {url}: {e}")
            return None

    def scrape_category(
        self,
        category: str = "companies",
        max_pages: int = 1,
        max_articles: Optional[int] = None,
        show_progress: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Scrapes articles from a specific Moneycontrol category across multiple pages.
        """
        category_articles = []
        logger.info(f"Starting scrape for category '{category}' up to {max_pages} pages...")

        page_range = range(1, max_pages + 1)
        if show_progress:
            page_range = tqdm(page_range, desc=f"Category: {category}")

        for page in page_range:
            items = self.fetch_listing_urls(category=category, page=page)
            self._sleep()

            for item in items:
                if max_articles and len(category_articles) >= max_articles:
                    break

                if item["url"] in self.seen_urls:
                    continue

                article_data = self.fetch_article_detail(item)
                if article_data:
                    category_articles.append(article_data)
                    self.articles_data.append(article_data)

                self._sleep()

            if max_articles and len(category_articles) >= max_articles:
                break

        logger.info(f"Completed '{category}'. Scraped {len(category_articles)} valid articles.")
        return category_articles

    def scrape_all_categories(
        self,
        categories: Optional[List[str]] = None,
        pages_per_category: int = 2,
        max_articles_per_category: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Scrapes articles across multiple specified categories.
        """
        if categories is None:
            categories = ["companies", "stocks"]

        total_scraped = []
        for cat in categories:
            results = self.scrape_category(
                category=cat,
                max_pages=pages_per_category,
                max_articles=max_articles_per_category,
            )
            total_scraped.extend(results)

        return total_scraped

    def to_dataframe(self) -> pd.DataFrame:
        """Returns scraped articles as a pandas DataFrame."""
        if not self.articles_data:
            return pd.DataFrame(columns=["Headlines", "Article", "Published_At", "Source", "Category", "URL"])
        return pd.DataFrame(self.articles_data)

    def save_csv(self, filepath: str) -> None:
        """Saves scraped articles to CSV."""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Successfully saved {len(df)} articles to '{filepath}'.")

    def save_json(self, filepath: str, indent: int = 2) -> None:
        """Saves scraped articles to a formatted JSON file."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.articles_data, f, ensure_ascii=False, indent=indent)
        logger.info(f"Successfully saved {len(self.articles_data)} articles to JSON '{filepath}'.")

    def save_jsonl(self, filepath: str) -> None:
        """Saves scraped articles to JSON Lines (JSONL) format for streaming and LLM ingestion."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            for item in self.articles_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"Successfully saved {len(self.articles_data)} articles to JSONL '{filepath}'.")
