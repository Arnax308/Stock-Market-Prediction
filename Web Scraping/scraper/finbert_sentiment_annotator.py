"""
FinBERT Financial Sentiment Annotator for Indian Financial News Dataset.
Utilizes the pre-trained 'ProsusAI/finbert' model running locally on NVIDIA GPU.
Adds:
- Sentiment: 'Positive', 'Negative', 'Neutral'
- Sentiment_Score: Float between -1.0 (strongly bearish) and +1.0 (strongly bullish)
- Sentiment_Confidence: Float between 0.0 and 1.0 (probability of predicted class)
"""

import os
import sys
import time
import logging
import torch
import pandas as pd
import numpy as np
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "ProsusAI/finbert"
BATCH_SIZE = 64
MAX_LENGTH = 128

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.json")
OUTPUT_JSONL = os.path.join(BASE_DIR, "Datasets", "financial_news_ner_annotated.jsonl")


def main():
    logger.info("Initializing FinBERT Sentiment Pipeline...")
    
    # 1. Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Target Compute Device: {device}")
    if device.type == "cuda":
        logger.info(f"GPU Name: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM Allocated: {torch.cuda.memory_allocated(0)/(1024**2):.1f} MB / {torch.cuda.get_device_properties(0).total_memory/(1024**2):.1f} MB")

    # 2. Load Tokenizer & Model
    logger.info(f"Loading weights for '{MODEL_NAME}' from Hugging Face...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    # FinBERT label mapping: 0 -> positive, 1 -> negative, 2 -> neutral
    id2label = model.config.id2label
    logger.info(f"Model ID-to-Label configuration: {id2label}")

    # 3. Load dataset
    logger.info(f"Reading input dataset: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    logger.info(f"Loaded {len(df):,} total records.")

    headlines = df["Headlines"].fillna("").astype(str).tolist()
    total_items = len(headlines)

    sentiments = []
    sentiment_scores = []
    confidences = []

    start_time = time.time()
    logger.info(f"Beginning batched sentiment inference (Batch size: {BATCH_SIZE})...")

    # 4. Batched inference with no_grad
    with torch.no_grad():
        for i in range(0, total_items, BATCH_SIZE):
            batch_texts = headlines[i : i + BATCH_SIZE]
            
            # Tokenize batch
            inputs = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt"
            ).to(device)

            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1).cpu().numpy()

            # Map probabilities
            # FinBERT config: 0: positive, 1: negative, 2: neutral
            pos_idx = [k for k, v in id2label.items() if v.lower() == "positive"][0]
            neg_idx = [k for k, v in id2label.items() if v.lower() == "negative"][0]
            neu_idx = [k for k, v in id2label.items() if v.lower() == "neutral"][0]

            for p in probs:
                pos_prob = float(p[pos_idx])
                neg_prob = float(p[neg_idx])
                neu_prob = float(p[neu_idx])

                # Continuous score: P(pos) - P(neg) in [-1.0, 1.0]
                signed_score = round(pos_prob - neg_prob, 4)
                
                # Discrete class: argmax
                max_idx = int(np.argmax(p))
                label = id2label[max_idx].capitalize()
                conf = round(float(p[max_idx]), 4)

                sentiments.append(label)
                sentiment_scores.append(signed_score)
                confidences.append(conf)

            if (i // BATCH_SIZE) % 20 == 0 or (i + BATCH_SIZE) >= total_items:
                processed = min(i + BATCH_SIZE, total_items)
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {processed:,} / {total_items:,} ({processed/total_items*100:.1f}%) | Speed: {rate:.1f} headlines/sec")

    elapsed_total = time.time() - start_time
    logger.info(f"Completed inference on {total_items:,} headlines in {elapsed_total:.2f}s ({total_items/elapsed_total:.1f} headlines/sec).")

    # 5. Attach new columns
    df["Sentiment"] = sentiments
    df["Sentiment_Score"] = sentiment_scores
    df["Sentiment_Confidence"] = confidences

    # 6. Save updated datasets
    logger.info(f"Saving updated dataset to {OUTPUT_CSV}...")
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    df.to_json(OUTPUT_JSON, orient="records", indent=2, force_ascii=False)
    df.to_json(OUTPUT_JSONL, orient="records", lines=True, force_ascii=False)

    logger.info("Distribution of Extracted Sentiments:")
    print(df["Sentiment"].value_counts())
    print("\nSummary Statistics of Sentiment_Score:")
    print(df["Sentiment_Score"].describe())
    logger.info("All files successfully updated!")


if __name__ == "__main__":
    main()
