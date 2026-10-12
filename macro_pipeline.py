"""
Macroeconomic and Large-Cap Financial Data Ingestion Pipeline.
Collects and aligns 3-5 years of daily financial data for:
- Commodities: Brent Crude (BZ=F), Gold (GC=F)
- Currencies: USD/INR (INR=X)
- Benchmark: NIFTY 50 (^NSEI)
- Top 10 Indian Large Caps (held for multi-year horizons: Reliance, TCS, HDFC Bank, Infosys, etc.)
"""

import os
import logging
from typing import List, Optional
import pandas as pd
import numpy as np
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TOP_10_LARGE_CAPS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "HINDUNILVR.NS",
    "BHARTIARTL.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "LICI.NS",
    "ITC.NS",
]

MACRO_SYMBOLS = {
    "Brent_Crude": "BZ=F",
    "Gold": "GC=F",
    "USD_INR": "INR=X",
    "NIFTY_50": "^NSEI",
}


def download_macro_and_financial_data(
    large_caps: Optional[List[str]] = None,
    period: str = "3y",
    output_csv: str = "Datasets/macro_financial_3y.csv",
) -> pd.DataFrame:
    """
    Downloads historical daily prices for macro factors and large-cap stocks.
    Performs forward-fill for international holiday mismatches and aligns dates.
    Computes key macroeconomic return, volatility, and correlation features.
    """
    if large_caps is None:
        large_caps = TOP_10_LARGE_CAPS

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    all_tickers = list(MACRO_SYMBOLS.values()) + large_caps
    logger.info(f"Downloading {period} daily historical data for {len(all_tickers)} tickers...")

    raw_data = yf.download(all_tickers, period=period, interval="1d", group_by="ticker", auto_adjust=True)

    # Extract Close prices
    close_dfs = {}
    for name, sym in MACRO_SYMBOLS.items():
        if sym in raw_data.columns.levels[0]:
            close_dfs[name] = raw_data[sym]["Close"]

    for sym in large_caps:
        clean_name = sym.replace(".NS", "")
        if sym in raw_data.columns.levels[0]:
            close_dfs[f"{clean_name}_Close"] = raw_data[sym]["Close"]
            close_dfs[f"{clean_name}_Volume"] = raw_data[sym]["Volume"]

    aligned_df = pd.DataFrame(close_dfs)

    # NIFTY 50 trading days serve as Indian market master calendar
    if "NIFTY_50" in aligned_df.columns:
        aligned_df = aligned_df.dropna(subset=["NIFTY_50"]).copy()

    # Forward fill commodities/currency (handles global vs domestic holiday gaps)
    aligned_df = aligned_df.ffill().bfill()

    logger.info("Computing macroeconomic returns and rolling technical signals...")

    # 1. Macro Percentage Returns (1-day, 5-day, 21-day/1-month)
    for asset in ["Brent_Crude", "Gold", "USD_INR", "NIFTY_50"]:
        if asset in aligned_df.columns:
            aligned_df[f"{asset}_Ret_1d"] = aligned_df[asset].pct_change(1)
            aligned_df[f"{asset}_Ret_5d"] = aligned_df[asset].pct_change(5)
            aligned_df[f"{asset}_Ret_21d"] = aligned_df[asset].pct_change(21)
            aligned_df[f"{asset}_Vol_20d"] = aligned_df[f"{asset}_Ret_1d"].rolling(20).std() * np.sqrt(252)

    # 2. Rolling Macro Shock Indicators
    if "Brent_Crude_Ret_5d" in aligned_df.columns:
        aligned_df["Crude_Shock_High"] = (aligned_df["Brent_Crude_Ret_5d"] > 0.05).astype(int)
        aligned_df["Crude_Shock_Low"] = (aligned_df["Brent_Crude_Ret_5d"] < -0.05).astype(int)

    if "Gold_Ret_5d" in aligned_df.columns:
        aligned_df["Gold_Surge"] = (aligned_df["Gold_Ret_5d"] > 0.03).astype(int)

    if "USD_INR_Ret_5d" in aligned_df.columns:
        aligned_df["Rupee_Depreciation"] = (aligned_df["USD_INR_Ret_5d"] > 0.01).astype(int)

    # 3. Rolling Correlations with NIFTY 50 (60-day window)
    if "NIFTY_50_Ret_1d" in aligned_df.columns:
        for macro in ["Brent_Crude", "Gold", "USD_INR"]:
            col = f"{macro}_Ret_1d"
            if col in aligned_df.columns:
                aligned_df[f"Corr_{macro}_NIFTY_60d"] = aligned_df[col].rolling(60).corr(aligned_df["NIFTY_50_Ret_1d"])

    aligned_df.index.name = "Date"
    aligned_df.reset_index(inplace=True)
    aligned_df["Date"] = pd.to_datetime(aligned_df["Date"]).dt.strftime("%Y-%m-%d")

    aligned_df.to_csv(output_csv, index=False)
    logger.info(f"Successfully saved macro dataset to '{output_csv}' with shape {aligned_df.shape}.")
    return aligned_df


if __name__ == "__main__":
    df = download_macro_and_financial_data(period="3y")
    print(df.tail())
