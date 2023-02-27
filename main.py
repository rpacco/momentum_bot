import pandas as pd
from datetime import datetime, date
import src.visualization.visualize as vz
import src.auxiliary.auxiliary as aux
import src.data.wrangling as w
import src.data.database as db

from flask import Flask, request
import telebot
import os
from ratelimit import limits, sleep_and_retry


API = os.getenv("API_KEY")

# SQL db data
host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
database = os.getenv("database") 
db_port = os.getenv("db_port")

bot = telebot.TeleBot(API)
app = Flask(__name__)
URL = "https://momentumbot.onrender.com"


# Set the rate limit to 1 message per second
@sleep_and_retry
@limits(calls=1, period=1)
def send_message(chat_id, text):
    bot.send_message(chat_id=chat_id, text=text)

# Set the rate limit to 1 message per second
@sleep_and_retry
@limits(calls=1, period=1)
def send_photo(chat_id, photo):
    bot.send_photo(chat_id=chat_id, photo=photo)


@bot.message_handler(commands=["IBOVESPA", "SP500", "NASDAQ"])
def handle_commands(mensagem):
    # defining portfolio build date begin
    port_date_begin = datetime.now()
    # sending calculating msg to the user
    calculating_msg(mensagem, port_date_begin)
    # connecting to sql database
    conn = db.conn_db(host, user, password, database, db_port)
    # retrieving last row from database where eq_index = command
    last_row = db.last_row_db(conn, mensagem)
    if last_row is None or last_row[1].strftime("%m-%Y") != port_date_begin.strftime("%m-%Y"):
        # wrangle index stocks
        stocks_list = w.wrangle_stocks(mensagem.text.replace('/', ''))
        # wrangling financial data for the index stocks
        stocks_data = w.wrangle(stocks_list)
        # momentum calculation for each stock belonging to the index
        # creating empty momentum variables
        list_coef = []
        list_score = []
        no_fit = []                              
        for d in stocks_data:
            try:  
                # storing slope coefficient and the score of the R² (determination coefficient)
                coef, score = aux.fit_reg(stocks_data[d])
                list_coef.append(coef)
                list_score.append(score)
            except:
                no_fit.append(d)
                list_coef.append(0)
                list_score.append(0)
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
        # inserting data into a SQL table called "monthly_portfolios"
        first_day_month = date(port_date_begin.year, port_date_begin.month, 1).strftime("%Y-%m-%d")
        try:    
            db.insert_data_db(first_day_month, conn, mensagem, momentum_stocks)
        finally:
            conn.close()
        # sending the bullet answer and the month-to-date cumulative returs graph
        send_message(
            mensagem.chat.id,
            aux.create_answer(momentum_stocks)
        )
        # sending cumulative returns graph
        send_photo(
            mensagem.chat.id,
            photo = vz.cumret_plot(momentum_stocks, mensagem.text.replace("/", ""))
        )
        
    
    else:
        conn.close()
        assets = [last_row[2], last_row[3], last_row[4], last_row[5], last_row[6]]
        send_message(
            mensagem.chat.id,
            aux.create_answer(assets)
        )
        # sending cumulative returns graph
        send_photo(
            mensagem.chat.id,
            photo = vz.cumret_plot(assets, mensagem.text.replace("/", ""))
        )


def calculating_msg(mensagem, date):
    # sending a imediate response to the user in order to inform that the calculation has begun
    send_message(
        mensagem.chat.id, 
        f"Calculating momentum portfolio for {date.strftime('%B-%Y')} based on {mensagem.text.replace('/', '')} index..."
    )


@bot.message_handler(func=lambda message: True)
def responder(message):
    text= ( 
            f"Hi {message.from_user.first_name}! This bot calculates the top-5 momentum assets of a reference index and returns "+
            "a month-to-date cumulative returns graph based on a equal-weighted portfolio holding those assets.\n"+
            "You must select one of the following reference index in order to "+
            "have a momentum portfolio calculated:\n/SP500\n/NASDAQ\n/IBOVESPA"
        )
    send_message(message.chat.id, text)

@app.route('/' + API, methods=['POST'])
def getMessage():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL + API)
    return "!", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))



