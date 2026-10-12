import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Optional, Set
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moneycontrol_scraper import MoneycontrolScraper
from rss_scraper import FinancialRSSScraper
from reddit_scraper import RedditFinancialScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_YEARS = {2024, 2025, 2026}

# Top 30 Indian Large Caps (NIFTY 50 heavyweights) + Macro Catalysts
LARGE_CAP_KEYWORDS = [
    # Tier 1 Heavyweights
    "Reliance Industries",
    "Tata Consultancy Services TCS",
    "HDFC Bank",
    "Infosys",
    "ICICI Bank",
    "State Bank of India SBI",
    "ITC Limited",
    "Bharti Airtel",
    "Hindustan Unilever HUL",
    "Larsen Toubro LT",
    # Tier 2 Large Caps
    "Kotak Mahindra Bank",
    "Axis Bank",
    "Tata Motors",
    "Sun Pharma",
    "Maruti Suzuki",
    "NTPC Limited",
    "ONGC Oil Natural Gas",
    "Power Grid Corporation",
    "Tata Steel",
    "Bajaj Finance",
    "Titan Company",
    "Mahindra Mahindra MM",
    "Asian Paints",
    "Adani Enterprises",
    "Adani Ports",
    "Coal India",
    "UltraTech Cement",
    "Wipro",
    "Tech Mahindra",
    "Bajaj Finserv",
    # Macroeconomic & Market Drivers
    "Crude Oil Indian economy inflation",
    "Brent crude oil prices India",
    "Gold prices India market demand",
    "RBI monetary policy repo rate inflation",
    "Indian Rupee dollar exchange rate",
    "NIFTY 50 earnings quarterly profits",
    "Sensex stock market rally crash",
    "FII DII inflow outflow Indian stocks",
]

OUTPUT_CSV = "Datasets/scraped_financial_news.csv"
OUTPUT_JSONL = "Datasets/scraped_financial_news.jsonl"
OUTPUT_JSON = "Datasets/scraped_financial_news.json"


def parse_and_validate_year(date_str: str) -> Optional[int]:
    """Parse date and return year if valid, else None."""
    if not date_str:
        return None
    cleaned = str(date_str).replace(" IST", "").strip()
    try:
        dt = pd.to_datetime(cleaned, format="ISO8601")
        return dt.year
    except Exception:
        pass
    try:
        dt = pd.to_datetime(cleaned)
        return dt.year
    except Exception:
        pass
    for y in ALLOWED_YEARS:
        if str(y) in cleaned:
            return y
    return None


def is_allowed_date(date_str: str) -> bool:
    """Check if date is strictly within 2024, 2025, or 2026."""
    yr = parse_and_validate_year(date_str)
    return yr in ALLOWED_YEARS


def load_existing_records() -> tuple[Set[str], List[dict]]:
    """Loads existing clean 2024-2026 records to prevent duplicate scraping."""
    seen_urls = set()
    records = []

    if os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
            for _, row in df.iterrows():
                u = str(row["URL"]).strip()
                date_val = str(row.get("Published_At", "")).strip()
                if u and u != "nan" and is_allowed_date(date_val):
                    seen_urls.add(u)
                    records.append(row.to_dict())
            logger.info(f"Loaded {len(records)} existing clean 2024-2026 records from {OUTPUT_CSV}.")
        except Exception as e:
            logger.warning(f"Could not load existing CSV: {e}")

    return seen_urls, records


def run_scaled_collection(
    target_count: int = 5000,
    start_year: int = 2024,
    end_year: int = 2026,
    include_rss_history: bool = True,
    include_reddit: bool = True,
    include_moneycontrol: bool = True,
):
    seen_urls, all_records = load_existing_records()
    logger.info(f"Starting news collection (2024-2026). Current clean records: {len(all_records)} | Target: {target_count}")

    # 1. Historical Google News RSS by Date Windows (2024, 2025, 2026)
    if include_rss_history and len(all_records) < target_count:
        logger.info(f"--- Stage 1: Harvesting Historical News ({start_year}-{end_year}) across {len(LARGE_CAP_KEYWORDS)} Topics ---")
        rss_scraper = FinancialRSSScraper()

        for kw in LARGE_CAP_KEYWORDS:
            if len(all_records) >= target_count:
                break

            logger.info(f"Harvesting historical news for: '{kw}'...")
            items = rss_scraper.fetch_historical_by_date_ranges(
                keywords=[kw],
                start_year=start_year,
                end_year=end_year,
                quarterly=True,
                max_items_per_chunk=100,
            )

            new_count = 0
            for item in items:
                u = item.get("URL", "").strip()
                pub_date = item.get("Published_At", "").strip()

                if u and u not in seen_urls and is_allowed_date(pub_date):
                    seen_urls.add(u)
                    item["Word_Count"] = len(item.get("Article", "").split())
                    all_records.append(item)
                    new_count += 1

            logger.info(f"Added {new_count} valid 2024-2026 articles for '{kw}'. Total now: {len(all_records)}/{target_count}")
            _save_checkpoint(all_records)

    # 2. Reddit Financial Subreddits (Retail Sentiment)
    if include_reddit and len(all_records) < target_count:
        logger.info("--- Stage 2: Collecting Retail Sentiment across 7 Subreddits ---")
        reddit_scraper = RedditFinancialScraper(delay_between_requests=2.5)
        reddit_posts = reddit_scraper.fetch_all_subreddits(
            feeds=["hot", "top"],
            time_filters=["year", "all"],
            max_posts_per_feed=30,
        )

        new_count = 0
        for post in reddit_posts:
            u = post.get("URL", "").strip()
            pub_date = post.get("Published_At", "").strip()

            if u and u not in seen_urls and is_allowed_date(pub_date):
                seen_urls.add(u)
                post["Word_Count"] = len(post.get("Article", "").split())
                all_records.append(post)
                new_count += 1

        logger.info(f"Added {new_count} valid Reddit posts. Total now: {len(all_records)}/{target_count}")
        _save_checkpoint(all_records)

    # 3. Moneycontrol Category Deep Pagination (Recent 2026 coverage)
    if include_moneycontrol and len(all_records) < target_count:
        logger.info("--- Stage 3: Moneycontrol Category Scraping (2026) ---")
        mc_scraper = MoneycontrolScraper(delay_range=(0.3, 0.8))
        mc_scraper.seen_urls = set(seen_urls)

        for cat in ["companies", "stocks", "markets", "economy", "earnings"]:
            if len(all_records) >= target_count:
                break

            logger.info(f"Scraping Moneycontrol category '{cat}' (up to 20 pages)...")
            articles = mc_scraper.scrape_category(
                category=cat,
                max_pages=20,
                show_progress=True,
            )

            new_count = 0
            for art in articles:
                u = art.get("URL", "").strip()
                pub_date = art.get("Published_At", "").strip()

                if u and u not in seen_urls and is_allowed_date(pub_date):
                    seen_urls.add(u)
                    art["Word_Count"] = len(art.get("Article", "").split())
                    all_records.append(art)
                    new_count += 1

            logger.info(f"Added {new_count} valid 2026 articles from '{cat}'. Total now: {len(all_records)}/{target_count}")
            _save_checkpoint(all_records)

    _save_checkpoint(all_records)
    logger.info(f"=== Great Scraping Complete! Total Verified 2024-2026 Articles: {len(all_records)} ===")


def _save_checkpoint(records: List[dict]):
    """Saves records to CSV, JSON, and JSONL formats with strict deduplication and null-checks."""
    if not records:
        return
    df = pd.DataFrame(records)
    # Filter to strictly 2024, 2025, 2026
    df["_Year"] = df["Published_At"].apply(parse_and_validate_year)
    df = df[df["_Year"].isin(ALLOWED_YEARS)].drop(columns=["_Year"])
    df.drop_duplicates(subset=["URL"], inplace=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    df.to_json(OUTPUT_JSON, orient="records", indent=2, force_ascii=False)
    df.to_json(OUTPUT_JSONL, orient="records", lines=True, force_ascii=False)


if __name__ == "__main__":
    run_scaled_collection(target_count=5000, start_year=2024, end_year=2026)
