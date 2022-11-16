import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import io
from datetime import date
from pandas.tseries.offsets import BMonthEnd


def cumret_plot(tickers_list):
    buf = io.BytesIO()

    tickers = tickers_list
    tickers.append("^BVSP")
    start_date = pd.to_datetime(date.today() + BMonthEnd(-1))
    end_date = pd.to_datetime(date.today())
    df = yf.download(tickers, start=start_date, end=end_date)["Adj Close"].pct_change().dropna()
    ret_portfolio = (np.cumprod(1 + df[["PRIO3.SA", "CYRE3.SA", "RRRP3.SA", "POSI3.SA", "SBSP3.SA"]].mean(axis=1))-1)*100
    ret_ibov = (np.cumprod(1 + df["^BVSP"])-1)*100
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1)
    ret_port = (np.cumprod(1 + df[["PRIO3.SA", "CYRE3.SA", "RRRP3.SA", "POSI3.SA", "SBSP3.SA"]].mean(axis=1))-1)*100
    ret_ibov = (np.cumprod(1 + df["^BVSP"])-1)*100
    ax.plot(ret_port, label="Momentum Portfolio")
    ax.plot(ret_ibov, label="Ibovespa")
    plt.text(ret_port.index[-1], ret_port[-1], str(round(ret_port[-1], 2)) + "%", ha="center")
    plt.text(ret_ibov.index[-1], ret_ibov[-1], str(round(ret_ibov[-1], 2)) + "%", ha="center")
    plt.ylabel("Cumulative returns (%)", fontsize=18)
    plt.xlabel("Date", fontsize=18)
    plt.title("Momentum portfolio returns", fontsize=20)
    plt.legend()
    plt.xticks(rotation=30)
    fig.savefig(buf, format="png")
    plt.close(fig)

    return buf


    
    