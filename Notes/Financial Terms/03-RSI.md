---
Title: RSI
Created: 26th September 2024 16:49
Last Modified: 26th September 2024 16:49
tags:
  - ML
  - StockMarket
cssclasses:
---
# RSI

It stands for Relative Strength Index. 

RSI is used to find whether a stock is oversold, overbought or neutral. If its value is over 70, it implies that the stock is overbought. On the other hand if its value is below 30, it implies that the stock is oversold. 

It is relatively easy to understand, but for calculating it can be a bit troublesome. 

For now the my RSI graph looks like this: 

![[Pasted image 20240927102347.png]]

I am suppose to make it prettier but in all honesty it can't get much better.

You can see 2 lines on the graph, the red dotted line on 70 and the blue dotted line on 30. This lines indicate the extremities. If the RSI value is above 70, it means the stock is overbought and if the value is below 30, it is oversold. 

---

# *What I did*



## *Calculations*

To calculate the RSI value, the most basic thing that you need to have is gains and losses. The using those 2, you get relative strength and then after you get the relative strength you apply a mathematical formula to get the RSI value. 

But for calculating RSI, you need to consider mean of the gains and losses of 14 days. There is only one mean which considers the previous data points, we need to find exponential weighted mean.

I found a very interesting way, to find gains and losses. How do you label something as a gain, loss or neutral? By comparing it with the previous day. I can't use ewm().mean() since I don't need the mean, but rather only the differences. 

That is when I learned about .diff() method. It does exactly what it name says, it finds differences. It finds difference between consecutive elements for each element of the array, then it returns a array consisting of all the calculated values. 

Now, I can easily sort between the gains and the losses. Every positive value is a gain and every negative value is a loss.

Now since I mentioned we need data of 14 days to calculate RSI, their is no way to determine the value for the first 13 days. At first I let them be, ie literally ignored them and then proceeded to calculate values from the 14th day. 

At first my answers seemed fine, but the more I tested it with different companies I realised my answer and the actual RSI values differ by large. This is when Phind suggested me to take simple average of the first 13 days and then do the calculations. 

As I outlined earlier, finding RSI is a long chain of calculations. We need to find avg_gains and avg_loss for 14 days to calculate the value of RSI. 

```python
for i in range(window, len(data)):
	avg_gain = (avg_gain * (window - 1) + gain.iloc[i]) / window
	avg_loss = (avg_loss * (window - 1) + loss.iloc[i]) / window
```

For context, gain and loss are arrays consisting of values from the .diff(), I calculated earlier. `avg_gain` and `avg_loss` are defined as the average of the first 13 days, that I talked about earlier. `window` is the no of days from which you want to calculate the RSI, by default its value is 14, but it can be changed as per need. 

`data` is the dataframe that consist of the financial data, obtained from calling the API. 

The above formula looks a bit similar to EMA. I obtained these formulas through internet and some research. I am not completely sure but I do believe we are calculating EMA but slightly in a different manner. 

Now, you get the relative strength using the formula: 

$$
\text{RS} = \frac{\text{avg\_gain}}{\text{avg\_loss}}
$$

Now we get to calculate the RSI, atlast. This can be done by using this formula: 

$$
RSI = 100 - \left( \frac{100}{1 + \text{RS}} \right)
$$


After all of this, you can now go and plot the graph for RSI. 

## *Prediction*

Predicting is easy, if the RSI value is above 70 then the stock is overbought and hence needs to be sold, likewise if it is below 30 it is oversold and hence needs to be bought. If its near 50, you need to hold.


# Updates

![[Pasted image 20240927151228.png]]

Tried making the RSI graph better, I guess it does look a bit better