import psycopg2

def conn_db(hostname, username, user_password, data_base, port_n):
    # establish connection to the database
    conn = psycopg2.connect(
        host=hostname,
        user=username,
        password=user_password,
        database=data_base,
        port=port_n
    )
    return conn

def last_row_db(connection, eq_index):
    # Retrieve the last row from the table
    cursor = connection.cursor()
    query = f'''
            SELECT * FROM monthly_portfolios 
            WHERE eq_index = '{eq_index}'
            ORDER BY month DESC
            LIMIT 1;
            '''
    cursor.execute(query)
    last_row = list(cursor.fetchone())
    cursor.close()

    return last_row


def insert_data_db(first_day_month, conn, eq_index, momentum_stocks):
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO monthly_portfolios (eq_index, month, asset1, asset2, asset3, asset4, asset5) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
            (eq_index, first_day_month, momentum_stocks[0], momentum_stocks[1], momentum_stocks[2], momentum_stocks[3], momentum_stocks[4])
        )
    conn.commit()

    return