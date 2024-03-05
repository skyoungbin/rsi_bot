from ta.momentum import RSIIndicator


def get_rsi(close, period):
    df_rsi = RSIIndicator(close, window=period).rsi()
    df_rsi = df_rsi.round(2) 
    return df_rsi

def calculate_return(initial_price, current_price):
    return_rate = (current_price - initial_price) / initial_price
    return return_rate

def calculate_profit(return_rate, investment):
    profit = return_rate  * investment
    return profit








