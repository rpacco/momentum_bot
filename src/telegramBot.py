from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd
import yfinance as yf
from datetime import date, timedelta
import matplotlib.pyplot as plt
from pandas.tseries.offsets import BMonthEnd, BMonthBegin
from sklearn.linear_model import LinearRegression
import numpy as np

load_dotenv()

class TelegramBot:
    def __init__(self):
        TOKEN = os.getenv("api_key")
        self.url = f"https://api.telegram.org/bot{TOKEN}/"

    def start(self):
        update_id = None
        while True:
            update = self.get_message(update_id)
            messages = update["result"]
            list_coef = []
            list_score = []
            if messages:
                for message in messages:
                    try:
                        update_id = message["update_id"]
                        chat_id = message["message"]["from"]["id"]
                        message_text = message["message"]["text"]
                        date = pd.to_datetime(int(message["message"]["date"]), unit="ms")
                        port_date_begin = (date - BMonthBegin()).strftime("%B-%Y")
                        self.send_answer(chat_id, f"Calculating momentum portfolio for {port_date_begin}...")  
                        stocks_list = self.wrangle_stocks()
                        stocks_data = self.wrangle(stocks_list)
                        for d in stocks_data:
                            coef, score = self.fit_reg(stocks_data[d])
                            list_coef.append(coef)
                            list_score.append(score)
                        momentum = [x*y for x, y in zip(list_coef, list_score)]
                        momentum_stocks = pd.DataFrame(
                                                            {
                                                            "lr_coef": list_coef,
                                                            "lr_r2": list_score,
                                                            "momentum": momentum
                                                            },
                                                            index=stocks_data.columns
                                                        ).sort_values("momentum", ascending=False).head(5).index.to_list()
                        answer_bot = self.create_answer(momentum_stocks)
                        self.send_answer(chat_id, answer_bot)
                    except:
                        pass
    
    def wrangle_stocks(self):
        url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
        stocks = [str(x) + ".SA" for x in pd.json_normalize(requests.get(url).json()["results"])["cod"].to_list()]
        return stocks
    
    def wrangle(self, stocks_list):
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
        X = np.asarray(range(0, len(stock_data.index))).reshape(-1, 1)
        y = np.log1p(stock_data)
        reg = LinearRegression()
        reg.fit(X, y)
        return reg.coef_[0], reg.score(X, y)
    
    def get_message(self, update_id):
        link_request = f"{self.url}getUpdates?timeout=1000"
        if update_id:
            link_request = f"{self.url}getUpdates?timeout=1000&offset={update_id + 1}"
        result = requests.get(link_request)
        return json.loads(result.content)

    def create_answer(self, momentum_stocks):
        return "".join(f"- {stock}\n" for stock in momentum_stocks).replace(".SA", "")

    def send_answer(self, chat_id, answer):
        link_to_send = f"{self.url}sendMessage?chat_id={chat_id}&text={answer}"
        requests.get(link_to_send)
        return