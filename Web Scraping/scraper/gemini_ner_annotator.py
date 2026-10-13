import os
import sys
import json
import time
import signal
import logging
import argparse
import requests
import pandas as pd
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Config
API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    logger.warning("GEMINI_API_KEY environment variable is not set. Set via: os.environ['GEMINI_API_KEY'] = 'your_key'")

MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-flash-latest",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV = os.path.join(BASE_DIR, "Datasets", "scraped_financial_news.csv")
CHECKPOINT_CSV = os.path.join(BASE_DIR, "Datasets", "scraped_financial_news_ner_checkpoint.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.json")
OUTPUT_JSONL = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.jsonl")


def call_gemini(prompt: str, max_retries: int = 5) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
        },
    }
    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries):
        for model in MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif resp.status_code == 429:
                    time.sleep(2.0 * (attempt + 1))
                elif resp.status_code == 503:
                    continue  # Fallback to next model
            except requests.RequestException:
                time.sleep(1.0)
        time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Gemini API failed after {max_retries} retries across models.")


def analyze_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prompt = f"""You are an expert financial market analyst specializing in Indian equities.
For each news item below, extract:
1. "Company": Name of the primary company mentioned, or "None" if general macro/market news.
2. "Sector": Primary industry sector (Energy, Banking, Information Technology, Automotive, Pharmaceuticals, FMCG, Macro / Economy, etc.), or "None".
3. "Interest": Binary integer (1 or 0).
   - Set to 1 if relevant to Indian large-cap companies (Nifty 50, BSE 100, blue chips) OR key macroeconomic market drivers (Crude Oil, Gold, RBI, Inflation, Union Budget, FII flows).
   - Set to 0 if penny/micro-cap, irrelevant, or non-commercial.

Input Items:
{json.dumps(batch, indent=2)}

Respond ONLY with a JSON array conforming to this schema:
[
  {{"id": integer, "Company": string, "Sector": string, "Interest": integer}},
  ...
]"""
    raw = call_gemini(prompt)
    try:
        return json.loads(raw)
    except Exception:
        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)


def run_pipeline(batch_size: int = 20, limit: Optional[int] = None):
    logger.info(f"Loading input dataset: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    logger.info(f"Loaded {len(df):,} total records.")

    annotated: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(CHECKPOINT_CSV):
        try:
            chk = pd.read_csv(CHECKPOINT_CSV)
            for _, r in chk.iterrows():
                u = str(r.get("URL", "")).strip()
                if u and pd.notna(r.get("Interest")):
                    annotated[u] = {
                        "Company": str(r.get("Company", "None")),
                        "Sector": str(r.get("Sector", "None")),
                        "Interest": int(r.get("Interest", 0)),
                    }
            logger.info(f"Resumed from checkpoint: {len(annotated):,} records already annotated.")
        except Exception as e:
            logger.warning(f"Error reading checkpoint: {e}")

    pending = []
    for idx, row in df.iterrows():
        u = str(row.get("URL", "")).strip()
        if u not in annotated:
            pending.append({
                "row_index": idx,
                "url": u,
                "headline": str(row.get("Headlines", "")).strip(),
            })

    if limit:
        pending = pending[:limit]
        logger.info(f"Limiting execution to {limit} records.")

    total_pending = len(pending)
    logger.info(f"Starting NER & Interest annotation for {total_pending:,} records (Batch size: {batch_size})")

    def save_checkpoint():
        rows = []
        for _, row in df.iterrows():
            u = str(row.get("URL", "")).strip()
            if u in annotated:
                d = row.to_dict()
                d.update(annotated[u])
                rows.append(d)
        if rows:
            pd.DataFrame(rows).to_csv(CHECKPOINT_CSV, index=False)
            logger.info(f"Saved checkpoint with {len(rows):,} annotations.")

    # Graceful exit handler
    def handle_sigint(sig, frame):
        logger.info("Signal received, saving checkpoint before exiting...")
        save_checkpoint()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    for i in range(0, total_pending, batch_size):
        batch = pending[i : i + batch_size]
        query = [{"id": item["row_index"], "headline": item["headline"]} for item in batch]

        try:
            results = analyze_batch(query)
            id_map = {r["id"]: r for r in results if "id" in r}
            for item in batch:
                res = id_map.get(item["row_index"], {})
                annotated[item["url"]] = {
                    "Company": res.get("Company", "None"),
                    "Sector": res.get("Sector", "None"),
                    "Interest": int(res.get("Interest", 0)),
                }
        except Exception as e:
            logger.warning(f"Batch {i//batch_size} error: {e}. Falling back to single queries...")
            for item in batch:
                try:
                    res = analyze_batch([{"id": item["row_index"], "headline": item["headline"]}])
                    if res:
                        r0 = res[0]
                        annotated[item["url"]] = {
                            "Company": r0.get("Company", "None"),
                            "Sector": r0.get("Sector", "None"),
                            "Interest": int(r0.get("Interest", 0)),
                        }
                    else:
                        annotated[item["url"]] = {"Company": "None", "Sector": "None", "Interest": 0}
                except Exception:
                    annotated[item["url"]] = {"Company": "None", "Sector": "None", "Interest": 0}

        done_count = min(i + batch_size, total_pending)
        if (i // batch_size) % 10 == 0 or done_count == total_pending:
            logger.info(f"Progress: {done_count:,} / {total_pending:,} annotated.")
            save_checkpoint()

        time.sleep(0.5)

    # Save final results
    logger.info("Merging annotated columns into final datasets...")
    df_out = df.copy()
    df_out["Company"] = df_out["URL"].apply(lambda u: annotated.get(str(u).strip(), {}).get("Company", "None"))
    df_out["Sector"] = df_out["URL"].apply(lambda u: annotated.get(str(u).strip(), {}).get("Sector", "None"))
    df_out["Interest"] = df_out["URL"].apply(lambda u: annotated.get(str(u).strip(), {}).get("Interest", 0))

    df_out.to_csv(OUTPUT_CSV, index=False)
    df_out.to_json(OUTPUT_JSON, orient="records", indent=2, force_ascii=False)
    df_out.to_json(OUTPUT_JSONL, orient="records", lines=True, force_ascii=False)
    logger.info(f"Successfully exported final annotated datasets:")
    logger.info(f"  CSV:   {OUTPUT_CSV}")
    logger.info(f"  JSON:  {OUTPUT_JSON}")
    logger.info(f"  JSONL: {OUTPUT_JSONL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Flash NER & Large-Cap Interest Annotator")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size per Gemini API call")
    parser.add_argument("--limit", type=int, default=None, help="Max records to process (default: all)")
    args = parser.parse_args()

    run_pipeline(batch_size=args.batch_size, limit=args.limit)
