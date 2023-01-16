import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import io
from datetime import date
from pandas.tseries.offsets import BMonthEnd


def cumret_plot(tickers_list):
    # creating buffer in memory to save the plot
    buf = io.BytesIO()
    # defining start and end date to calculate the portfolio returns
    start_date = pd.to_datetime(date.today() + BMonthEnd(-1))
    end_date = pd.to_datetime(date.today())
    # wrangling month-to-date portfolio + benchmark data
    df = yf.download(tickers_list + ["^BVSP"], start=start_date, end=end_date, auto_adjust=True)[["Open", "Close"]]
    # defining returns for the portfolio, considering that the investor buys at Open on the first trading day of the month
    df_ret = pd.concat(
        [df["Open"].iloc[0, :].to_frame().T, 
        df["Close"].iloc[0:, :]]
    ).pct_change().dropna()
    # creating figure
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_subplot(1, 1, 1)
    # calculating cumulative returns of momentum portfolio and benchmark
    ret_port = (np.cumprod(1 + df_ret[[value for value in tickers_list if value != "^BVSP"]].mean(axis=1))-1)*100
    ret_ibov = (np.cumprod(1 + df_ret["^BVSP"])-1)*100
    # plotting cumulative returns
    ax.plot(ret_port, label="Momentum Portfolio")
    ax.plot(ret_ibov, label="Ibovespa")
    # adding informative cumulative return text at the last trading day available
    plt.text(ret_port.index[-1], ret_port[-1], str(round(ret_port[-1], 2)) + "%", ha="center")
    plt.text(ret_ibov.index[-1], ret_ibov[-1], str(round(ret_ibov[-1], 2)) + "%", ha="center")
    # adding labels and title
    plt.ylabel("Cumulative returns (%)", fontsize=18)
    plt.xlabel("Date", fontsize=18)
    plt.title("Momentum portfolio returns", fontsize=20)
    plt.legend()
    plt.xticks(rotation=30)
    # saving the plot to buffer and closing it
    fig.savefig(buf, format="png")
    plt.close(fig)

    return buf
    