import re
import os
import json
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def repair_existing_dataset(csv_path: str = "Datasets/scraped_financial_news.csv"):
    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    initial_len = len(df)
    logger.info(f"Loaded {initial_len} rows from {csv_path}")

    # 1. Remove corrupt video placeholder rows (e.g. headline 'business', url containing /videos/ or /video/)
    video_mask = df["URL"].str.contains(r"/video(?:s)?/", case=False, na=False) & (
        df["Published_At"].isna() | (df["Published_At"].str.strip() == "") | (df["Headlines"].str.strip().str.lower() == "business")
    )
    dropped_count = video_mask.sum()
    df = df[~video_mask].copy()
    logger.info(f"Removed {dropped_count} corrupt video rows.")

    # 2. Repair missing timestamps on the remaining rows
    missing_mask = df["Published_At"].isna() | (df["Published_At"].str.strip() == "")
    missing_indices = df[missing_mask].index

    session = requests.Session()
    session.headers.update(HEADERS)

    for idx in missing_indices:
        url = df.loc[idx, "URL"]
        headline = df.loc[idx, "Headlines"]
        logger.info(f"Attempting to repair date for: {headline} ({url})")

        found_date = None
        try:
            r = session.get(url, timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")

                # Try JSON-LD
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        raw = script.string or script.get_text()
                        if raw:
                            data = json.loads(raw)
                            items = data if isinstance(data, list) else [data]
                            for it in items:
                                if isinstance(it, dict) and it.get("datePublished"):
                                    found_date = str(it["datePublished"]).strip()
                                    break
                        if found_date:
                            break
                    except Exception:
                        pass

                # Try meta tags
                if not found_date:
                    m = soup.find("meta", property="og:article:published_time") or soup.find("meta", attrs={"name": "publish-date"})
                    if m and m.get("content"):
                        found_date = m["content"].strip()
        except Exception as e:
            logger.warning(f"Error fetching URL {url}: {e}")

        # Fallback to date in URL
        if not found_date:
            match = re.search(r"(\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})", url)
            if match:
                found_date = match.group(1)

        if found_date:
            df.loc[idx, "Published_At"] = found_date
            logger.info(f"Successfully recovered date: {found_date}")
        else:
            logger.warning(f"Could not recover date for index {idx}. URL: {url}")

    # Remove any remaining rows with missing timestamps
    still_missing = df["Published_At"].isna() | (df["Published_At"].str.strip() == "")
    if still_missing.sum() > 0:
        logger.warning(f"Dropping {still_missing.sum()} unrecoverable rows to maintain clean dataset integrity.")
        df = df[~still_missing].copy()

    # Save cleaned files
    df.to_csv(csv_path, index=False, encoding="utf-8")
    json_path = csv_path.replace(".csv", ".json")
    jsonl_path = csv_path.replace(".csv", ".jsonl")
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)
    df.to_json(jsonl_path, orient="records", lines=True, force_ascii=False)

    logger.info(f"Successfully repaired dataset! Clean rows: {len(df)} (from initial {initial_len}). Missing dates remaining: 0.")

if __name__ == "__main__":
    repair_existing_dataset()
