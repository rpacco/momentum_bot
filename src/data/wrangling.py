import requests
import json
import pandas as pd
import yfinance as yf
from datetime import date
from pandas.tseries.offsets import BMonthEnd, BMonthBegin

def wrangle_stocks(message_text):
    '''
    This function is used to retrieve a list of stocks from specific API endpoints (Brazilian stock exchange, B3; Wikipedia webiste for SP500 and NASDAQ index ETFs).

    Input: None

    Output: List of stocks
    '''
    if message_text == "IBOVESPA":
        url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
        stocks = [str(x) + ".SA" for x in pd.json_normalize(requests.get(url).json()["results"])["cod"].to_list()]
    elif message_text == "SP500":
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df_raw = pd.read_html(url)
        stocks = df_raw[0]["Symbol"].replace("BRK.B", "BRK-B").replace("BF.B", "BF-B").to_list() # replace to fix tickers to yfinance format
    else:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100#Differences_from_NASDAQ_Composite_index"
        df_raw = pd.read_html(url)
        stocks = df_raw[4]["Ticker"].replace("BRK.B", "BRK-B").replace("BF.B", "BF-B").to_list()
    
    return stocks

def wrangle(stocks_list):
    '''
    Input:
        stocks_list : list of stocks

    Output:
        data : filtered dataset of adjusted closing prices of stocks

    This function wrangle financial data from Yfinance module, related to all index assets.
    It filters out the stocks which are trading below its 100-day moving average price.
    Also, the data time series of the data are related to 4 months daily lookback closing prices
    The function starts by defining two variables lday_pvm and fday_4pvm, which are respectively, 
    '''
    #last day from previous month
    lday_pvm = pd.to_datetime(date.today() + BMonthEnd(-1))
    #first day from 4th previous months
    fday_4pvm = pd.to_datetime(date.today() + BMonthBegin(-4))
    df = yf.download(stocks_list, start=fday_4pvm, end=lday_pvm)["Adj Close"]
    # filter in stocks above 100 average price
    mask = (df.iloc[-1,: ] > df.iloc[-100: , :].mean())
    df_filtered = df.loc[:, mask]
    data = df_filtered[fday_4pvm:lday_pvm]
    
    return data