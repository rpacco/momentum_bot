from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd
import yfinance as yf
from datetime import date, datetime
import matplotlib.pyplot as plt
from pandas.tseries.offsets import BMonthEnd, BMonthBegin
from sklearn.linear_model import LinearRegression
import numpy as np
import src.visualization.visualize as vz
import mysql.connector

class TelegramBot:
    def __init__(self):
        # importing Telegram bot token and assigning to variable
        TOKEN = os.environ["api_key"]
        self.url = f"https://api.telegram.org/bot{TOKEN}/"

    def start(self):
        # creating empty variable to store a unique identifier for each incoming update from a user.
        update_id = None
        # importing mySQL database variables and storing to each variable
        host = os.environ["host"]
        user = os.environ["user"]
        password = os.environ["password"]
        database = os.environ["database"]
        port = os.environ["port"]
        try:
            while True:
                # get updated id data from telegram bot user
                update = self.get_message(update_id)
                # get message data
                messages = update["result"]
                
                if messages:
                    for message in messages:
                        try:
                            # retireving main data from user message
                            update_id = message["update_id"]
                            chat_id = message["message"]["from"]["id"]
                            message_text = message["message"]["text"].upper().replace('/', '')

                            # default response for wrong user message
                            if message_text not in ["SP500", "NASDAQ", "IBOVESPA"]:
                                self.send_answer(chat_id, 
                                    "Hi! This bot calculates the top-5 momentum assets of an index and returns "+
                                    "a month-to-date cumulative returns graph based on a equal-weighted portfolio holding those assets.\n"+
                                    "You must select one of the following index in order to "+
                                    "have a momentum portfolio:\n/SP500\n/NASDAQ\n/IBOVESPA")
                            
                            # reponse for index selection by the user
                            else:
                                # defining the date which the investor should build its momentum portfolio
                                port_date_begin = datetime.utcfromtimestamp(message["message"]["date"])

                                # sending a imediate response to the user in order to inform that the calculation has begun
                                self.send_answer(chat_id, 
                                f"Calculating momentum portfolio for {port_date_begin.strftime('%B-%Y')} based on {message_text} index...")  

                                # establish connection to the database
                                conn = mysql.connector.connect( 
                                    host = host, 
                                    user = user, 
                                    password = password, 
                                    database = database, 
                                    port = port
                                )
                                # Retrieve the last row from the table
                                cursor = conn.cursor()
                                query = f"SELECT * FROM monthly_portfolios_{message_text.lower()} ORDER BY id DESC LIMIT 1"
                                cursor.execute(query)
                                last_row = cursor.fetchone()
                                cursor.close()

                                # If no data is found or its date is prior than the portfolio reference date, insert calculated data into the database
                                if last_row is None or last_row[1].strftime("%m-%Y") != port_date_begin.strftime("%m-%Y"):
                                    # wrangle index stocks
                                    stocks_list = self.wrangle_stocks()
                                    # wrangling financial data for the index stocks
                                    stocks_data = self.wrangle(stocks_list)
                                    # momentum calculation for each stock belonging to the index
                                    try:
                                        # creating empty momentum variables
                                        list_coef = []
                                        list_score = []
                                        for d in stocks_data:
                                            # storing slope coefficient and the score of the R² (determination coefficient)
                                            coef, score = self.fit_reg(stocks_data[d])
                                            list_coef.append(coef)
                                            list_score.append(score)
                                    except:
                                        pass
                                    # creating momentum coef
                                    momentum = [x*y for x, y in zip(list_coef, list_score)]
                                    # sorting the stocks by its momentum coefficient (the higher the coefficient higher its momentum) and picking the top 5 assets
                                    momentum_stocks = pd.DataFrame(
                                                                        {
                                                                        "lr_coef": list_coef,
                                                                        "lr_r2": list_score,
                                                                        "momentum": momentum
                                                                        },
                                                                        index=stocks_data.columns
                                                                    ).sort_values("momentum", ascending=False).head(5).index.to_list()
                                    # creating bullet answer of the 5-asset that will build the momentum portfolio
                                    answer_bot = self.create_answer(momentum_stocks)
                                    # sending the bullet answer and the month-to-date cumulative returs graph
                                    self.send_answer(chat_id, answer_bot)
                                    self.send_figure(chat_id, vz.cumret_plot(momentum_stocks, message_text))
                                    # inserting data into a SQL table called "monthly_portfolios"
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        f"INSERT INTO monthly_portfolios_{message_text.lower()} (month, asset1, asset2, asset3, asset4, asset5) VALUES (%s, %s, %s, %s, %s, %s)", 
                                        (port_date_begin.strftime('%Y-%m-%d'), momentum_stocks[0], momentum_stocks[1], momentum_stocks[2], momentum_stocks[3], momentum_stocks[4]))
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    
                                else:
                                    # storing assets tickers retrived from SQL database into a list
                                    assets = [last_row[2], last_row[3], last_row[4], last_row[5], last_row[6]]
                                    # creating bullet answer of the 5-asset that will build the momentum portfolio
                                    answer_bot = self.create_answer(assets)
                                    # sending the bullet answer and the month-to-date cumulative returs graph
                                    self.send_answer(chat_id, answer_bot)
                                    self.send_figure(chat_id, vz.cumret_plot(assets))
                                    conn.close()
                                    
                        except:
                            pass
        except:
            pass

        return 
    
    def wrangle_stocks(self, message_text):
        '''
        This function is used to retrieve a list of stocks from specific API endpoints (Brazilian stock exchange, B3; Blackrock webiste for SP500 and NASDAQ index ETFs).

        Input: None

        Output: List of stocks
        '''
        if message_text == "IBOVESPA":
            url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
            stocks = [str(x) + ".SA" for x in pd.json_normalize(requests.get(url).json()["results"])["cod"].to_list()]
        if message_text == "SP500":
            url = "https://www.blackrock.com/us/individual/products/239726/ishares-core-sp-500-etf/1464253357814.ajax?tab=all&fileType=json"
            response = requests.get(url)
            decoded_data = response.content.decode('utf-8-sig')
            data = json.loads(decoded_data)
            df_raw = pd.DataFrame(data["aaData"])
            stocks = df_raw[df_raw[3] == "Equity"][0].to_list()
        else:
            url = "https://www.blackrock.com/pt/profissionais/products/253741/ishares-nasdaq-100-ucits-etf/1547863479665.ajax?tab=all&fileType=json"
            response = requests.get(url)
            decoded_data = response.content.decode('utf-8-sig')
            data = json.loads(decoded_data)
            df_raw = pd.DataFrame(data["aaData"])
            stocks = df_raw[df_raw[3] == "Equity"][0].to_list()
        return stocks
    
    def wrangle(self, stocks_list):
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
        mask = (df.iloc[-1,: ] > df.iloc[-100: , :].mean())
        df_filtered = df.loc[:, mask]
        data = df_filtered[fday_4pvm:lday_pvm]
        return data

    def fit_reg(self, stock_data):
        # convert range of index of stock_data into array and reshape it to a column vector
        X = np.asarray(range(0, len(stock_data.index))).reshape(-1, 1)
        # apply logarithm function to stock_data closing prices, in order to normalize it
        y = np.log1p(stock_data)
        #create a LinearRegression instance and fitting it to the data
        reg = LinearRegression()
        reg.fit(X, y)

        return reg.coef_[0], reg.score(X, y)
    
    def get_message(self, update_id):
        '''
        function to return the content of the last message sent to the bot
        '''
        link_request = f"{self.url}getUpdates?timeout=1000"
        if update_id:
            link_request = f"{self.url}getUpdates?timeout=1000&offset={update_id + 1}"
        result = requests.get(link_request)
        return json.loads(result.content)

    def create_answer(self, momentum_stocks):
        # creating bullet formatted response of the momentum portfolio stocks
        return "".join(f"- {stock}\n" for stock in momentum_stocks).replace(".SA", "")

    def send_answer(self, chat_id, answer):
        # sending bullet text message to the user
        link_to_send = f"{self.url}sendMessage?chat_id={chat_id}&text={answer}"
        requests.get(link_to_send)
        return

    def send_figure(self, chat_id, answer):
        # sending cumulative returns graph to the user
        answer.seek(0)
        requests.post(f"{self.url}sendPhoto?chat_id={chat_id}", files=dict(photo=answer))
        answer.close()
        return