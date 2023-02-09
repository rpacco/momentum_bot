import requests
import json
import pandas as pd
import yfinance as yf
from datetime import date
from pandas.tseries.offsets import BMonthEnd, BMonthBegin

def wrangle_stocks(message_text):
    '''
    This function is used to retrieve a list of stocks from specific API endpoints (Brazilian stock exchange, B3; Blackrock webiste for SP500 and NASDAQ index ETFs).

    Input: None

    Output: List of stocks
    '''
    if message_text == "IBOVESPA":
        url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
        stocks = [str(x) + ".SA" for x in pd.json_normalize(requests.get(url).json()["results"])["cod"].to_list()]
    elif message_text == "SP500":
        url = "https://www.blackrock.com/us/individual/products/239726/ishares-core-sp-500-etf/1464253357814.ajax?tab=all&fileType=json"
        response = requests.get(url)
        decoded_data = response.content.decode('utf-8-sig')
        data = json.loads(decoded_data)
        df_raw = pd.DataFrame(data["aaData"])
        stocks = df_raw[df_raw[3] == "Equity"][0].replace("BRKB", "BRK-B").replace("BFB", "BF-B").to_list() # replace to fix tickers to yfinance format
    else:
        url = "https://www.blackrock.com/pt/profissionais/products/253741/ishares-nasdaq-100-ucits-etf/1547863479665.ajax?tab=all&fileType=json"
        response = requests.get(url)
        decoded_data = response.content.decode('utf-8-sig')
        data = json.loads(decoded_data)
        df_raw = pd.DataFrame(data["aaData"])
        stocks = df_raw[df_raw[3] == "Equity"][0].replace("BRKB", "BRK-B").replace("BFB", "BF-B").to_list() # replace to fix tickers to yfinance format
    
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