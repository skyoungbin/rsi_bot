import pandas as pd
from dateutil import tz

from ta.momentum import RSIIndicator

import comm_.tool_util as tool_util


# 데이터프레임 변환
def calc_df(df):
    df = df.reindex(index=df.index[::-1]).reset_index()
    df = df.rename(columns={
        'timestamp': 'timestamp',
        'candle_date_time_kst': 'time',
        'opening_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'trade_price': 'close',
        'candle_acc_trade_price': 'volume',
        })
    df = df[['timestamp', 'time', 'open', 'high', 'low', 'close', 'volume']]

    df['time'] = pd.to_datetime(df['time'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    # 한국 시간대(KST, UTC+9)로 변경
    df['timestamp'] = df['timestamp'].dt.tz_convert(tz.gettz('Asia/Seoul'))
    
    df.set_index('time', inplace=True)
    return df


def get_rsi(close, period=14):
    df_rsi = RSIIndicator(close, window=period).rsi()
    df_rsi = df_rsi.round(2) 
    return df_rsi

def calculate_return(initial_price, current_price):
    return_rate = (current_price - initial_price) / initial_price
    return return_rate

def calculate_profit(return_rate, investment):
    profit = return_rate  * investment
    return profit


def calculate_count_from_days_ago(interval_minutes, days_ago):
    """
    :param interval_minutes: 데이터 포인트 간의 간격 (분 단위)
    :param days_ago: 현재로부터 몇 일 전까지의 데이터를 가져올지 지정

    """
    # 하루의 총 분 수를 계산
    minutes_in_a_day = 24 * 60
    
    # 총 필요한 데이터 포인트 수를 계산
    total_minutes = days_ago * minutes_in_a_day
    count = total_minutes // interval_minutes
    
    return count


def buy_order(orderbook, total_assets, ticker, trade_price):
    trade_time = tool_util.get_kr_time().isoformat()  # 실제 trade_time 값을 사용하십시오
    data = {
        "trade_time": [trade_time],
        "ticker": [ticker],
        "price": [trade_price],
        "position": ['long'],
        "total_assets": [total_assets],
        "return_rate": ['']
    }

    # 데이터프레임 생성 및 반환
    new_order = pd.DataFrame(data).set_index('trade_time')
    updated_orderbook = pd.concat([orderbook, new_order])

    purchase_status = True

    return data, updated_orderbook, purchase_status, total_assets

def sell_order(orderbook, total_assets, ticker, trade_price):
    trade_time = tool_util.get_kr_time().isoformat()  # 실제 trade_time 값을 사용하십시오
    return_rate = calculate_return(orderbook.iloc[-1]['price'], trade_price)
    updated_total_assets = total_assets + calculate_profit(return_rate, total_assets)

    data = {
        "trade_time": [trade_time],
        "ticker": [ticker],
        "price": [trade_price],
        "position": ['neutral'],
        "total_assets": [updated_total_assets],
        "return_rate": [return_rate * 100]
    }

    # 데이터프레임 생성 및 반환
    new_order = pd.DataFrame(data).set_index('trade_time')
    updated_orderbook = pd.concat([orderbook, new_order])

    purchase_status = False

    return data, updated_orderbook, purchase_status, updated_total_assets


