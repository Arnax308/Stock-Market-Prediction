---
Title: Fibonacci Retracement and Extension Levels
Created: 27th September 2024 15:13
Last Modified: 27th September 2024 15:13
tags:
  - ML
  - StockMarket
cssclasses:
---
# Fibonacci Retracement and Extension Levels

As a fellow leetcode dweller, I know my fibonacci series. It is calculated by adding the two previous numbers to obtain the current number. 

Another special thing about this series is if you divide 2 consecutive numbers you get a ratio of 1.618. The Golden Ratio.

So the fibonacci levels and the extension levels are derived from these ratios. 

If you take the ratio of a number i, with numbers bigger than i, then you get the values 0.236, 0.382, 0.618, 0.786. 

Similarly if you divide i with numbers small than i, then you get 1.236, 1.382, 1.618. 

It looks something like this: 
![[Pasted image 20240927153609.png]]

This one looks pretty right?? Its because god knows how many commits I have pushed trying to make this look better. I have spend countless afternoons, trying to make sure that the graph doesn't look congested. 


# *Fibonacci Retracement*

Converting this ratios to percentages, we obtain the so called levels. Which are:- 

- 23.6 %
- 38.2 %
- 50 % (Not a ratio, but still regarded as one of the levels)
- 61.8 %
- 78.6% 

So, now how does this work? Pretty easy tbh. Let's take a example: If a stock has a initial value of 100, then it rose from 100 to 200. But now, due to some reasons, the stock's price started to fall. 

Now, the difference is 200-100 = Rs 100. This difference is rather important. 

Now when the stock starts to fall, it will get its 1st support at 23.6% level. Now, how do you calculate the price at 23.6% level? Its rather simple, take the 23.6 % of the difference ie 23.6% of 100, which is Rs 23.6. Now you subtract this 23.6 Rs from the 200 (the high price), doing so we get Rs 176.4. 

Similarly you can calculate all the retracement levels. Pretty easy right?  

# Fibonacci Extension

Similarly the fibonacci extension levels, that we have are:-

- 123.6%
- 138.2%
- 150%
- 161.8%
- 200%

The retracement levels look for the stock when it falls. The extension levels look at when the stock rises. 

Consider our previous example, but only this time the stock rather than falling at 200, keeps rising. 

Now the stock will experience its first resistance. The calculation is same as above. Only this time you add rather than taking the difference. 

So for our stock, it will meet its 1st resistance at Rs 223.6 and then so on. 


# *What I did*


## Insight

I used a lot of formal terms like support and resistance, while these are the official words/terms, they seem a bit vague to a newcomer like me. 

So what does support mean? It means that stock's price which is plummeting down, would slow down here or even stop as well. But why would it stop magically??? It's not magic tbh, but it can be seen as a collective psychology. 

So when a stock is plummeting down, after a while its prices starts to become lower and lower. After a while, people realise that, this stock that used to cost this much, is now so cheap. So people start buying that stock and its value starts to increase. Even at the first level, that is 23.6%, its value is 23% lower than what it was. So, if I were to buy 500 stocks at 176.4 Rs, then I can sell it when it prices increases a bit. 

So the stock did fell till Rs 176.4, I bought 500 stocks of the same and when it reached its value of Rs 200, I sold it again, making a profit of 500 x Rs 24 = Rs 12000 on the way. 

So it's not magic, its just a lot of traders thinking at once that they can gain impressive profits from the same. 

Now similarly lets talk about resistance. It works the same but only in the opposite direction. Let us consider our example again, where the stock kept on rising even after reaching the price of 200. 

Now when the stock reaches the price of 223.6, it meets it's first resistance. Remember traders wants profit but they are not greedy. They know if a stock is flying high,it is gonna come crashing down some day. So when the price reaches 223.6. I will think I am already making huge profits, let's just sell now. I bought the stock at 200 and now when it reached 223, I know I can make huge profits selling this stock. 

The trader can buy/sell its stock at any point in the time, but having the fibonacci levels, ensures that most of the traders buy/sell the stock, when its price is coming near the levels. 

## Calculations

Fibonacci retracement even though sounds like one of the easiest things to calculate, but in reality it was super difficult to implement it. 

The problem with this indicator is, you can place it anywhere as per your need. I didn't know this at start. At first, I took the high_price as the max value present in the data and the low_price as the min value present in the data. 

Little did I know, how grave a mistake it was. After this, I learned about the placement thing and I also learned that their are different formulas for uptrend and downtrend. So, now I don't only have to figure out what I am analysing is a downtrend or a uptrend but also where to place it. 

So at first, I thought let's analyse the last trend, irrespective of the no of days. I was able to capture the trends and also calculate the levels, but the levels are too close to each other to actually make any sense. I was back at square 1. 

But this time, I am taking into the account the 2nd last trend, which allows me to analyse the last trend. Meaning I am calculating values of the 2nd last trend, so as to make decisions/analyse the last trend. 

The most important part is identifying trends. I am doing so by taking into the account a window of size 10. So, I compare each price with the price 10 days back. If the current price is larger, then it is a uptrend and is represented by the value 1, if the former price is bigger then it's a downtrend, represented by -1, and no changes are  indicated by 0. 

Now, I identified all the trends in the data, now we need to find from where the change in trends is occurring, using this the calculation would be much simpler and much more easier. 

So, I where the changes are occurring, by simply using np.diff(). Now, I used np.where() to the indices of said changes. These indices are stored in an array named `significant_changes`. Now, we know that any trend lasts from `significant_changes[i]` to `significant_changes[i+1]`. 

We finally know where all the trends are and what they are. Any value which is greater than 0 implies uptrend and any value smaller than 0 implies downtrend. 

Now we can easily pick the 2nd last trend and 