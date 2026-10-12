import logging
import re
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class RedditFinancialScraper:
    """
    Scraper for Indian financial subreddits (r/IndianStreetBets, r/IndiaInvestments).
    Captures retail trader psychology and sentiment, formatted directly into
    [Headlines, Article, Published_At, Source, Category, URL].
    """

    DEFAULT_SUBREDDITS = [
        "IndianStreetBets",
        "IndiaInvestments",
        "StockMarketIndia",
        "dalalstreet",
        "NSEbets",
        "IndianStockMarket",
        "ValueInvesting",
    ]

    BASE_RSS_URL = "https://www.reddit.com/r/{subreddit}/{feed}.rss"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/xml,text/xml,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self, timeout: int = 15, delay_between_requests: float = 2.0):
        self.timeout = timeout
        self.delay_between_requests = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.posts_data: List[Dict[str, str]] = []

    def _clean_reddit_content(self, html_content: str) -> str:
        """Strip HTML tags and boilerplate Reddit table/link artifacts."""
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove standard Reddit footer links (submitted by /u/... [link] [comments])
        for a in soup.find_all("a"):
            if "[link]" in a.get_text() or "[comments]" in a.get_text():
                a.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def fetch_subreddit_feed(
        self,
        subreddit: str = "IndianStreetBets",
        feed: str = "hot",
        time_filter: Optional[str] = None,
        max_posts: int = 25,
        max_retries: int = 3,
    ) -> List[Dict[str, str]]:
        """
        Fetch posts from a subreddit RSS feed (feed can be: 'hot', 'new', 'top').
        time_filter can be: 'all', 'year', 'month', 'week' (when feed='top').
        """
        import time
        import subprocess

        url = self.BASE_RSS_URL.format(subreddit=subreddit, feed=feed)
        if feed == "top" and time_filter:
            url += f"?t={time_filter}"

        raw_xml = None
        for attempt in range(max_retries):
            try:
                res = self.session.get(url, timeout=self.timeout)
                if res.status_code == 200:
                    raw_xml = res.text
                    break
                elif res.status_code == 429:
                    wait_time = int(res.headers.get("x-ratelimit-reset", 5)) + (attempt * 3)
                    logger.warning(f"Reddit 429 Rate limit on r/{subreddit}. Backing off {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Reddit HTTP {res.status_code} for r/{subreddit}")
            except Exception as e:
                logger.debug(f"Requests error on r/{subreddit}: {e}")

            # Fallback to curl
            try:
                proc = subprocess.run(
                    ["curl.exe", "-s", "-L", "-A", self.DEFAULT_HEADERS["User-Agent"], url],
                    capture_output=True,
                    timeout=self.timeout + 2,
                )
                stdout_str = proc.stdout.decode("utf-8", errors="ignore")
                if proc.returncode == 0 and "<entry>" in stdout_str:
                    raw_xml = stdout_str
                    break
            except Exception:
                pass

            time.sleep(2 * (attempt + 1))

        if not raw_xml:
            logger.warning(f"Failed to fetch Reddit feed for r/{subreddit} after retries")
            return []

        try:
            # Parse XML feed
            soup = BeautifulSoup(raw_xml, "xml")
            entries = soup.find_all("entry")
            subreddit_posts = []

            for entry in entries[:max_posts]:
                title_tag = entry.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""

                # Skip daily discussion threads or bot wikis
                if "daily discussion thread" in title.lower() and "wiki" in title.lower():
                    continue

                link_tag = entry.find("link")
                post_url = link_tag.get("href", "") if link_tag else ""

                updated_tag = entry.find("updated") or entry.find("published")
                published_at = updated_tag.get_text(strip=True) if updated_tag else ""

                content_tag = entry.find("content")
                raw_content = content_tag.get_text(strip=True) if content_tag else ""
                clean_body = self._clean_reddit_content(raw_content)

                article_text = clean_body if len(clean_body) > 30 else f"Discussion on: {title}"

                record = {
                    "Headlines": title,
                    "Article": article_text,
                    "Published_At": published_at,
                    "Source": f"Reddit (r/{subreddit})",
                    "Category": "retail_sentiment",
                    "URL": post_url,
                }
                subreddit_posts.append(record)
                self.posts_data.append(record)

            logger.info(f"Fetched {len(subreddit_posts)} posts from r/{subreddit} ({feed})")
            return subreddit_posts

        except Exception as e:
            logger.error(f"Error parsing Reddit feed {url}: {e}")
            return []

    def fetch_all_subreddits(
        self,
        subreddits: Optional[List[str]] = None,
        feeds: Optional[List[str]] = None,
        time_filters: Optional[List[str]] = None,
        max_posts_per_feed: int = 25,
    ) -> List[Dict[str, str]]:
        """Fetch posts across multiple subreddits and feed types."""
        import time
        if subreddits is None:
            subreddits = self.DEFAULT_SUBREDDITS
        if feeds is None:
            feeds = ["hot", "top"]
        if time_filters is None:
            time_filters = ["year", "all"]

        all_posts = []
        for sub in subreddits:
            for feed in feeds:
                if feed == "top":
                    for tf in time_filters:
                        posts = self.fetch_subreddit_feed(
                            subreddit=sub, feed=feed, time_filter=tf, max_posts=max_posts_per_feed
                        )
                        all_posts.extend(posts)
                        time.sleep(self.delay_between_requests)
                else:
                    posts = self.fetch_subreddit_feed(
                        subreddit=sub, feed=feed, max_posts=max_posts_per_feed
                    )
                    all_posts.extend(posts)
                    time.sleep(self.delay_between_requests)

        return all_posts

    def to_dataframe(self) -> pd.DataFrame:
        """Returns scraped posts as a pandas DataFrame."""
        if not self.posts_data:
            return pd.DataFrame(columns=["Headlines", "Article", "Published_At", "Source", "Category", "URL"])
        return pd.DataFrame(self.posts_data)

    def save_csv(self, filepath: str) -> None:
        """Saves scraped posts to CSV."""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Successfully saved {len(df)} Reddit posts to '{filepath}'.")

    def save_json(self, filepath: str, indent: int = 2) -> None:
        """Saves scraped posts to a formatted JSON file."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.posts_data, f, ensure_ascii=False, indent=indent)
        logger.info(f"Successfully saved {len(self.posts_data)} Reddit posts to JSON '{filepath}'.")

    def save_jsonl(self, filepath: str) -> None:
        """Saves scraped posts to JSON Lines (JSONL) format."""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            for item in self.posts_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"Successfully saved {len(self.posts_data)} Reddit posts to JSONL '{filepath}'.")
