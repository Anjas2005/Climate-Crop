import yfinance as yf
import streamlit as st
import pandas as pd

st.write("""
# Simple Stock Price App
         
## Shown are  the stock price ***closing*** price and ***volume*** of Google!
""")

tickerSymbol ='GOOGL'

tickerData= yf.Ticker(tickerSymbol)

tickerDf= tickerData.history(period='1d', start='2010-5-31',end ='2024-12-12')


st.write("""
###  Closing Price
""")
st.line_chart(tickerDf.Close)

st.write("""
###  Volume
""")
st.line_chart(tickerDf.Volume)

st.write("""
## Shown are  the stock price ***closing*** price and ***volume*** of Apple!
""")
tickerSymbolA ='AAPL'

tickerDataA= yf.Ticker(tickerSymbolA)

tickerDfA= tickerDataA.history(period='1d', start='2010-5-31',end ='2024-12-12')


st.write("""
###  Closing Price
""")
st.line_chart(tickerDfA.Close)

st.write("""
###  Volume
""")
st.line_chart(tickerDfA.Volume)