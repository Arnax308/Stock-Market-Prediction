---
Title: MACD
Created: 26th September 2024 14:56
Last Modified: 26th September 2024 14:56
tags:
  - ML
  - StockMarket
cssclasses:
---
# MACD

MACD: Moving Average Convergence and Divergence

---
# *Overview* 

MACD is used for predicting if the stock price will rise or fall. The name is a bit scary but once you understand it, it's not really that hard. 

It looks something like this:
![[Pasted image 20240926150009.png]]


It looks prettier on moneycontrol site tbh. But I am proud of what I did with matplotlib.

So this graph consist of 3 things the MACD line (the blue line), the Signal line(the red line) and the histogram (the weird grey lines)

I tried making the histogram, a bit more histogramically but I kept breaking the graph, so it is what it is for now, will hopefully do something about this in future.

So now, when the MACD line cuts the signal line from above, the stock acts bearish ie the stock's price starts to fall. When the MACD line cuts the signal line from below, it starts acting bullish ie the stock's price starts to rise. 

So basically what needs to be done is check for the last cut and how long ago it happened. Using this we can predict if we need to sell, buy or hold. 

---
# *Components*


## MACD Line

This line is calculated with the help of 2 things. The moving average for 12 days and the moving average of 26 days. The 12-moving average is also called as the fast average and the 26 one is called as the slow average. 

So now, we take difference of both the averages (26_moving_average - 12_moving_average) and the resulting values are the ones which plot the line. 

Note: we take moving average of the 'Close' price. Every calculation in the stock market is more or less calculated on the close price. 

## Signal Line

This line is calculated by taking the moving average of 9 days. That's literally it. 

*Note*: The values for calculating the MACD line and the signal line can be literally anything ie user defined. But the values 26 and 12 for MACD and 9 for signal are standard and default. We can make them user-defined, it's not really that hard, but for now sticking with default values. 

## MACD Histogram

This is calculated by taking the difference of macd line and signal line. The histogram tell you about the difference between the two, that's it. 

It's literally `macd - signal`. 


This indicator is literally filled up with nothing but differences. But on the other hand, its easy to calculate and is quite effective, so no complains. 


# *What I did*

## Calculations

A quick google search tells you that, the moving average we are calculating are EMA(Exponential Moving Average) and not SMA(Simple Moving Average). 

Thanks to pandas, calculating the EMA is easier. I know how to calculate EMA mathematically and it is quite troublesome. So, again thanks to pandas I was saved from the trouble. 

I used ewm().mean() to calculate the moving averages. Another interesting thing I learned while using this is the parameter `adjusted`. 

So the basic concept of EMA is to take into account previous means as well. Simply saying calculating the EMA of the nth term will also include the EMA value of (n-1)th term. Also the more recent terms are given more weight(importance). 

Now, `adjusted=False` only takes into account only the previous term, but using `adjusted=True` will take into account the entire history of dataset. Basically for calculating the EMA of nth term, the values of entire dataset will be taken into account. 

Anyways using ewm().mean(), I got MAs of 12-days, 26-days and 9-days. Now taking the difference I obtained the MACD line and the signal line. 

Now taking the difference of MACD line and the signal line I got the histogram. This was being done for one year of data, so I obtained the values of MACD, Signal and the Histogram for each day. 

Now I can use matplotlib and draw a graph as shown above, pretty easily. But that's not where the stuff ends, I have to make predictions not simply gather data. 


## Predicting


At first, what I implemented was a bunch of if-else statements, the code was a bit messy and hence hard to debug. I couldn't get rid of the error on line 47, which apparently was a empty line. 

So I asked ChatGPT to debug my code and also clean it a bit to make it more manageable. This is when I came across np.where() function. In all honesty this just a if else statement but in one line. So what was a nested block of if-else came down to 2 lines of np.where(). Pretty cool, tbh. (The error was a missing `)` nothing much)

The conditions that ChatGPT gave me were a bit questionable but I got the basic idea thanks to it. I only needed to check 2 things for each day. The current macd value and the signal value and the previous day's macd value and signal value. Considering if they were equal, smaller or greater than each other, I could say buy, sell or hold. 

For now I am calculating for each day if the stock should be bought, sold or held. I am not sure, if any additional logic needs to be implemented but for now it's working. If I come across any edge case, I am sure to add any additional logic for sure!  


# Updates 

![[Pasted image 20240927151204.png]]

Made the graph a lot better xD 

