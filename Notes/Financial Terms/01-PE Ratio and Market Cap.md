---
Title: PE Ratio and Market Cap
Created: 26th September 2024 16:15
Last Modified: 26th September 2024 16:15
tags:
  - ML
  - StockMarket
cssclasses:
---
# PE Ratio

It stands for Profit-Earning Ratio. 

It basically means that what an investor is willing to pay for a stock, for earning Rs 1. Simply putting it perspective, a PE ratio of 20 implies that the investor is willing to pay Rs 20 to earn Rs 1. 

When a company demonstrates high P/E Ratio, it means that the company is overvalued. On the other hand, a low Price to Earnings Ratio signifies undervaluation of stocks. There are many different interpretations of PE ratio, but considering what I implemented, this interpretation explains it.

Its a bit abstract to understand from its definition. Lets look at its formula. 

P/E Ratio = (Current Market Price of a Share / Earnings per Share)

There are many different types of PE ratio, but what I am considering is Trailing PE ratio and/or Absolute PE ratio. 


---
# Market Cap

Its the total value of the company's stock. It is found by multiplying the price of stock into the total no of stocks. 

It is not net-worth of the company, it only tells about the total stock values of the company. 

Using market cap, a company is identified as small cap, mid cap or large cap. Any company having market cap below 5000 Cr is small cap, the company having market cap between 5000 Cr and 20000 Cr is mid cap and the company having more than 20000 Cr is large cap. (So many zeros, damn)

Although its not a official term, companies having market cap above 1 lakh Cr are called as blue chip companies. (Lakh Cr sounds so unreal)

---
# *What I did*

So at first I calculated the market cap. Due to some shallow researching I found that, the formula for PE ratio is `market_cap/ (eps * no_shares)`. 

So, it became evident that I need to find the market cap. I was gonna need it to identify whether a company is small, mid or large cap anyways. 

So finding market cap is not really a hard thing, you just need to find the current price of the stock and the total no of outstanding shares. Outstanding shares include share blocks held by institutional investors and restricted shares owned by the company’s officers and insiders.

Both of those values that can be directly obtained by the yfinance api, so I got both of those values and then multiplied them to get the market cap. 

Now I needed to find the pe ratio, as I mentioned earlier, I came across a different formula. So I tried searching for EPS, when I came across a bunch of different types of EPSes. A bit more researching told me that I was looking for trailing eps. 

So now after getting all the values, I found pe ratio. Since I am suppose to predict stuff and not just simply gather data, I found that a company having PE ratio greater than 20 implies selling. So now I check for if the PE ratio is greater than 20 then I scream SELL or else BUY.

Also I am using Market Cap to identify if a company is small cap, mid cap or large cap. 


