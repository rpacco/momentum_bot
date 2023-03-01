import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import yfinance as yf
import io
from datetime import date
from pandas.tseries.offsets import BMonthBegin


def cumret_plot(tickers_list, index):
    # creating buffer in memory to save the plot
    buf = io.BytesIO()
    # defining yfinance index_ticker dictionary
    index_ticker = {
        "IBOVESPA": "^BVSP",
        "SP500": "^GSPC",
        "NASDAQ": "^IXIC"
    }
    # defining start and end date to calculate the portfolio returns
    end_date = date.today()
    start_date = date(end_date.year, end_date.month, 1)
    # wrangling month-to-date portfolio + benchmark data
    df = yf.download(tickers_list + [index_ticker[index]], start=start_date, end=end_date, auto_adjust=True)[["Open", "Close"]]
    # defining month-to-date returns for the portfolio, considering that the investor buys at Open on the first trading day of the month
    df_ret = pd.concat(
        [df["Open"].iloc[0, :].to_frame().T, 
        df["Close"].iloc[0:, :]]
    ).pct_change().dropna()
    # calculating month-to-date cumulative returns of momentum portfolio and benchmark
    ret_port = (np.cumprod(1 + df_ret[[value for value in tickers_list if value != index_ticker[index]]].mean(axis=1))-1)*100
    ret_index = (np.cumprod(1 + df_ret[index_ticker[index]])-1)*100
    ret_alpha = ret_port - ret_index

    sns.set_style("darkgrid", {"grid.color": ".6", "grid.linestyle": ":"})
    # creating figure
    fig, ax = plt.subplots(figsize=(15, 8))

    # plotting cumulative returns
    sns.lineplot(data=ret_port, ax=ax, label="Momentum Portfolio")
    sns.lineplot(data=ret_index, ax=ax, label=index)
    sns.lineplot(data=ret_alpha, ax=ax, label="ALPHA strategy", linestyle="dashed", 
                color="green" if ret_alpha[-1] > 0 else "red")

    # adding informative cumulative return text at the last trading day available
    ax.text(ret_port.index[-1], ret_port[-1], str(round(ret_port[-1], 2)) + "%", ha="center")
    ax.text(ret_index.index[-1], ret_index[-1], str(round(ret_index[-1], 2)) + "%", ha="center")
    ax.text(ret_alpha.index[-1], ret_alpha[-1], str(round(ret_alpha[-1], 2)) + "%", ha="center")

    # adding labels and title
    ax.set(ylabel="Cumulative returns (%)", xlabel="Date", 
        title="Momentum portfolio returns")
    sns.set_context(rc={"font.size": 10,"axes.titlesize": 12 ,"axes.labelsize": 10})

    ax.legend()
    ax.tick_params(axis='x', rotation=30)

    # saving the plot to buffer and closing it
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return buf