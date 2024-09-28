---
Title: Yfinance
Created: 12th September 2024 11:18
Last Modified: 12th September 2024 11:18
tags:
  - ML
cssclasses:
---
# Documentation

Couldn't really find one with neat explanations, so made one. This is probably everything that I will need in this project.


## 1. Ticker Object Functions
When you create a `Ticker` object for a stock or other asset , you can access various pieces of information about that asset.

#### **`Creating a ticker`**

```python
tcs = yf.Ticker('TCS.NS')
```

#### a. **`history(period='1mo', interval='1d')`**
   - Retrieves historical market data (stock prices).
   - Parameters:
     - `period`: Time period for data retrieval (e.g., `1d`, `5d`, `1mo`, `1y`, etc.).
     - `interval`: Data interval (e.g., `1m` for minute data, `1d` for daily data).
     -

```python
   tcs.history(period="1mo", interval="1d")
   ```

#### b. **`info`**
   - Returns a dictionary of metadata about the company or asset, including market cap, industry, sector, etc.
   ```python
   tcs.info
   ```

#### c. **`actions`**
   - Returns a DataFrame with corporate actions like dividends and stock splits.
   ```python
   tcs.actions
   ```

#### d. **`dividends`**
   - Returns historical dividend data.
   ```python
   tcs.dividends
   ```

#### e. **`splits`**
   - Returns historical stock split data.
   ```python
   tcs.splits
   ```

#### f. **`sustainability`** X
   - Returns the company's sustainability ratings (environmental, social, governance) if available.
   ```python
   tcs.sustainability
   ```

#### g. **`recommendations`**
   - Returns analyst recommendations and ratings.
   ```python
   tcs.recommendations
   ```

#### h. **`earnings`**
   - Returns a DataFrame with historical earnings data, including earnings dates and earnings per share (EPS).
   ```python
   tcs.income_stmt
   ```

#### i. **`quarterly_earnings`**
   - Returns a DataFrame with quarterly earnings data.
   ```python
   tcs.quarterly_earnings
   ```

#### j. **`financials`**
   - Returns a DataFrame with the company's annual financial statements.
   ```python
   tcs.financials
   ```

#### k. **`quarterly_financials`**
   - Returns a DataFrame with the company's quarterly financial statements.
   ```python
   tcs.quarterly_financials
   ```

#### l. **`balance_sheet`**
   - Returns a DataFrame with the company's annual balance sheet.
   ```python
   tcs.balance_sheet
   ```

#### m. **`quarterly_balance_sheet`**
   - Returns a DataFrame with the company's quarterly balance sheet.
   ```python
   tcs.quarterly_balance_sheet
   ```

#### n. **`cashflow`**
   - Returns a DataFrame with the company's annual cash flow statement.
   ```python
   tcs.cashflow
   ```

#### o. **`quarterly_cashflow`**
   - Returns a DataFrame with the company's quarterly cash flow statement.
   ```python
   tcs.quarterly_cashflow
   ```

#### p. **`major_holders`**
   - Returns major shareholders in the company.
   ```python
   tcs.major_holders
   ```

#### q. **`institutional_holders`**
   - Returns a DataFrame with the company's institutional shareholders.
   ```python
   tcs.institutional_holders
   ```

#### r. **`mutualfund_holders`**
   - Returns a DataFrame with mutual funds that hold shares in the company.
   ```python
   tcs.mutualfund_holders
   ```

#### s. **`calendar`**
   - Returns a DataFrame with the company's next earnings date.
   ```python
   tcs.calendar
   ```

#### t. **`options`**  X
   - Returns a list of options expiration dates.
   ```python
   tcs.options
   ```

#### u. **`option_chain(expiration)`** X
   - Returns option chains for a specific expiration date (both calls and puts).
   ```python
   tcs.option_chain('2023-09-22')
   ```

#### v. **`news`**
   - Returns a list of recent news articles related to the company.
   ```python
   tcs.news
   ```

## 2. Multi-Ticker Functions
`yfinance` also allows you to download data for multiple tickers at once using `yf.download()`.

#### a. **`download(tickers, start=None, end=None, group_by='ticker')`**
   - Downloads historical market data for one or more tickers.
   - Parameters:
     - `tickers`: List or string of tickers.
     - `start`, `end`: Specify the start and end dates.
     - `group_by`: Choose to group the output by ticker or date.
-

   ```python
   yf.download(["TCS.NS", "INFY.NS"], start="2022-01-01", end="2023-01-01")
   ``` 

### 3. **Caching**
- **`cache_lookup_interval`**
  - Controls how long (in minutes) `yfinance` caches responses to improve performance and avoid making repeated API requests for the same data.

### 4. **Other Utility Functions**
- **`get_market_status()`** (Unofficial): Check whether the market is open or closed.
   ```python
   yf.get_market_status()
   ```

## Summary of Important Functions

| Function                   | Description                                       |
| -------------------------- | ------------------------------------------------- |
| `history()`                | Fetch historical market data                      |
| `info`                     | Get basic company information                     |
| `financials`               | Get company's annual financial statements         |
| `quarterly_financials`     | Get company's quarterly financial statements      |
| `balance_sheet`            | Get company's annual balance sheet                |
| `quarterly_balance_sheet`  | Get company's quarterly balance sheet             |
| `cashflow`                 | Get company's annual cash flow statement          |
| `quarterly_cashflow`       | Get company's quarterly cash flow statement       |
| `earnings`                 | Get company's annual earnings data                |
| `quarterly_earnings`       | Get company's quarterly earnings data             |
| `dividends`                | Get dividend data                                 |
| `splits`                   | Get stock split data                              |
| `recommendations`          | Get analyst recommendations and ratings           |
| `option_chain(expiration)` | Fetch options data for a specific expiration date |
| `download()`               | Download historical data for multiple tickers     |
| `news`                     | Get the latest news related to the company        |



