"""
Scraper dedicated to Reddit Community Sentiment and Multi-Outlet Financial RSS Feeds.
Collects from:
1. Reddit Subreddits: r/IndianStreetBets, r/IndiaInvestments, r/StockMarketIndia,
   r/dalalstreet, r/NSEbets, r/IndianStockMarket, r/ValueInvesting
2. Official Financial RSS Feeds:
   - Economic Times (Markets, Economy)
   - Livemint (Markets, Companies)
   - Business Standard (Markets)
   - Moneycontrol (Business, Top News)
3. Historical multi-outlet Google News RSS (Economic Times, Livemint) across 2024-2026

Strictly enforces:
- Date validation: 2024, 2025, 2026
- Polite delays for Reddit (no 429 blocks)
- Deduplication against existing dataset
"""

import os
import sys
import time
import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Set
import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reddit_scraper import RedditFinancialScraper
from rss_scraper import FinancialRSSScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_YEARS = {2024, 2025, 2026}
OUTPUT_CSV = "Datasets/scraped_financial_news.csv"
OUTPUT_JSONL = "Datasets/scraped_financial_news.jsonl"
OUTPUT_JSON = "Datasets/scraped_financial_news.json"

OFFICIAL_RSS_FEEDS = [
    {"source": "Economic Times (Markets)", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "cat": "markets"},
    {"source": "Economic Times (Economy)", "url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms", "cat": "economy"},
    {"source": "Livemint (Markets)", "url": "https://www.livemint.com/rss/markets", "cat": "markets"},
    {"source": "Livemint (Companies)", "url": "https://www.livemint.com/rss/companies", "cat": "companies"},
    {"source": "Business Standard (Markets)", "url": "https://www.business-standard.com/rss/markets-106.rss", "cat": "markets"},
    {"source": "Moneycontrol (Business)", "url": "https://www.moneycontrol.com/rss/business.xml", "cat": "business"},
]


def parse_and_validate_year(date_str: str) -> bool:
    if not date_str:
        return False
    cleaned = str(date_str).replace(" IST", "").strip()
    try:
        dt = pd.to_datetime(cleaned, format="ISO8601")
        return dt.year in ALLOWED_YEARS
    except Exception:
        pass
    try:
        dt = pd.to_datetime(cleaned)
        return dt.year in ALLOWED_YEARS
    except Exception:
        pass
    return any(str(y) in cleaned for y in ALLOWED_YEARS)


def load_seen_urls() -> tuple[Set[str], List[dict]]:
    seen = set()
    records = []
    if os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
            for _, row in df.iterrows():
                u = str(row["URL"]).strip()
                if u and u != "nan":
                    seen.add(u)
                    records.append(row.to_dict())
            logger.info(f"Loaded {len(records)} existing records from {OUTPUT_CSV}.")
        except Exception as e:
            logger.warning(f"Error reading existing CSV: {e}")
    return seen, records


def scrape_official_rss_feeds(seen_urls: Set[str]) -> List[dict]:
    """Scrapes direct RSS feeds from Economic Times, Livemint, Business Standard, etc."""
    logger.info("--- Ingesting Direct Official Financial RSS Feeds ---")
    new_items = []
    import email.utils

    for feed_info in OFFICIAL_RSS_FEEDS:
        src = feed_info["source"]
        url = feed_info["url"]
        cat = feed_info["cat"]
        logger.info(f"Fetching RSS: {src}...")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            items = root.findall(".//item")

            count = 0
            for item in items:
                title_tag = item.find("title")
                link_tag = item.find("link")
                pub_tag = item.find("pubDate")
                desc_tag = item.find("description")

                title = title_tag.text.strip() if title_tag is not None and title_tag.text else ""
                link = link_tag.text.strip() if link_tag is not None and link_tag.text else ""
                raw_pub = pub_tag.text.strip() if pub_tag is not None and pub_tag.text else ""
                desc = desc_tag.text.strip() if desc_tag is not None and desc_tag.text else ""

                if not title or not link or link in seen_urls:
                    continue

                # Parse date to ISO
                iso_date = raw_pub
                try:
                    p = email.utils.parsedate_to_datetime(raw_pub)
                    iso_date = p.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

                if not parse_and_validate_year(iso_date):
                    continue

                # Clean description
                desc_soup = BeautifulSoup(desc, "html.parser")
                clean_desc = desc_soup.get_text(strip=True)
                article_text = clean_desc if len(clean_desc) > 30 else title

                record = {
                    "Headlines": title,
                    "Article": article_text,
                    "Published_At": iso_date,
                    "Source": src,
                    "Category": cat,
                    "URL": link,
                    "Word_Count": len(article_text.split()),
                }
                seen_urls.add(link)
                new_items.append(record)
                count += 1

            logger.info(f"Added {count} items from {src}.")
        except Exception as e:
            logger.warning(f"Failed to fetch {src} ({url}): {e}")

        time.sleep(1.0)

    return new_items


def scrape_reddit_sentiment(seen_urls: Set[str]) -> List[dict]:
    """Scrapes retail discussions across 7 subreddits with rate-limit pacing."""
    logger.info("--- Scraping Retail Sentiment across 7 Subreddits ---")
    reddit_scraper = RedditFinancialScraper(timeout=15, delay_between_requests=5.0)
    new_items = []

    subreddits = [
        "IndianStreetBets",
        "IndiaInvestments",
        "StockMarketIndia",
        "dalalstreet",
        "NSEbets",
        "IndianStockMarket",
        "ValueInvesting",
    ]

    for sub in subreddits:
        logger.info(f"Scraping r/{sub}...")
        for feed in ["hot", "top"]:
            time_filter = "year" if feed == "top" else None
            posts = reddit_scraper.fetch_subreddit_feed(
                subreddit=sub,
                feed=feed,
                time_filter=time_filter,
                max_posts=30,
            )

            count = 0
            for p in posts:
                u = p.get("URL", "").strip()
                pub = p.get("Published_At", "").strip()
                if u and u not in seen_urls and parse_and_validate_year(pub):
                    seen_urls.add(u)
                    p["Word_Count"] = len(p.get("Article", "").split())
                    new_items.append(p)
                    count += 1

            logger.info(f"Added {count} posts from r/{sub} ({feed}).")
            time.sleep(5.0)  # Safe 5s delay prevents Reddit 429 rate limit

    return new_items


def scrape_multi_outlet_historical(seen_urls: Set[str]) -> List[dict]:
    """Scrapes historical news from Economic Times, Livemint, Business Standard across 2024-2026."""
    logger.info("--- Scraping Multi-Outlet Historical RSS (ET, Mint, BS) across 2024-2026 ---")
    rss = FinancialRSSScraper()
    new_items = []

    outlets = [
        "site:economictimes.indiatimes.com",
        "site:livemint.com",
        "site:business-standard.com",
    ]
    topics = [
        "Nifty 50 large cap earnings",
        "Reliance Industries",
        "HDFC Bank TCS",
        "Crude oil prices Indian economy",
        "Gold price India inflation",
        "RBI monetary policy repo rate",
    ]

    # Quarters across 2024-2026
    quarters = [
        ("2024-01-01", "2024-06-30"),
        ("2024-07-01", "2024-12-31"),
        ("2025-01-01", "2025-06-30"),
        ("2025-07-01", "2025-12-31"),
        ("2026-01-01", "2026-06-30"),
        ("2026-07-01", "2026-10-08"),
    ]

    for outlet in outlets:
        for topic in topics:
            for s_d, e_d in quarters:
                query = f"{topic} {outlet} after:{s_d} before:{e_d}"
                items = rss.fetch_feed(query=query, max_items=50)

                count = 0
                for it in items:
                    u = it.get("URL", "").strip()
                    pub = it.get("Published_At", "").strip()
                    if u and u not in seen_urls and parse_and_validate_year(pub):
                        seen_urls.add(u)
                        it["Word_Count"] = len(it.get("Article", "").split())
                        new_items.append(it)
                        count += 1

                time.sleep(0.5)

            logger.info(f"Harvested {len(new_items)} new multi-outlet items so far...")

    return new_items


def save_dataset(records: List[dict]):
    if not records:
        return
    df = pd.DataFrame(records)
    df.dropna(subset=["Headlines", "Article", "Published_At"], inplace=True)
    df = df[df["Headlines"].str.strip() != ""].copy()
    df.drop_duplicates(subset=["URL"], inplace=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    df.to_json(OUTPUT_JSON, orient="records", indent=2, force_ascii=False)
    df.to_json(OUTPUT_JSONL, orient="records", lines=True, force_ascii=False)
    logger.info(f"Saved total {len(df)} records to {OUTPUT_CSV}.")


def main():
    seen_urls, all_records = load_seen_urls()
    initial_count = len(all_records)
    logger.info(f"Starting Reddit & RSS Scraper. Initial records: {initial_count}")

    # 1. Scrape Multi-Outlet Historical RSS (Economic Times, Livemint, Business Standard for 2024-2026)
    historical_items = scrape_multi_outlet_historical(seen_urls)
    all_records.extend(historical_items)
    save_dataset(all_records)

    # 2. Scrape Direct Official RSS Feeds (ET, Mint, BS, MC)
    official_items = scrape_official_rss_feeds(seen_urls)
    all_records.extend(official_items)
    save_dataset(all_records)

    # 3. Scrape Reddit Subreddits
    reddit_items = scrape_reddit_sentiment(seen_urls)
    all_records.extend(reddit_items)
    save_dataset(all_records)

    added_total = len(all_records) - initial_count
    logger.info(f"Completed! Added {added_total} new Reddit & RSS records. Total dataset size: {len(all_records)}")


if __name__ == "__main__":
    main()
