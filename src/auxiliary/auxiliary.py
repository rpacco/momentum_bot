import numpy as np
from sklearn.linear_model import LinearRegression

def fit_reg(stock_data):
    # convert range of index of stock_data into array and reshape it to a column vector
    X = np.asarray(range(0, len(stock_data.index))).reshape(-1, 1)
    # apply logarithm function to stock_data closing prices, in order to normalize it
    y = np.log1p(stock_data)
    #create a LinearRegression instance and fitting it to the data
    reg = LinearRegression()
    reg.fit(X, y)

    return reg.coef_[0], reg.score(X, y)

def create_answer(momentum_stocks):
    # creating bullet formatted response of the momentum portfolio stocks
    return "".join(f"- {stock}\n" for stock in momentum_stocks).replace(".SA", "")