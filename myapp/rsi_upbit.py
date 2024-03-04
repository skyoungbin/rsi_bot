import requests
import pandas as pd
import time
import pyupbit
import datetime
import numpy as np
import os
import logging
import threading

import comm_.trade_util as trade_util

class tickerData:
    def __init__(self):

        self.ticker_df = pd.DataFrame()
        self.last_row = pd.DataFrame()
        self.last_bar = None
        self.wait = None
        self.candle = 30
        self.vol_high = 70
        self.vol_low = 40
        self.rsi_window = 14
        self.lock = threading.Lock()

    def get_state(self):
        return {"last_row": self.last_row.to_dict(orient='records'), "candle": self.candle, "vol_high": self.vol_high, "vol_low": self.vol_low, "rsi_window": self.rsi_window}
        

# RSI 알림 클래스 정의
class RsiNotifier:
    def __init__(self):
        self.update_all_tickers()
        self.tickers = ['KRW-BTC'] #, 'KRW-ETH', 'KRW-NEO'
        self.gen_tickers(self.tickers)

    #slack 메세지
    def set_slack(self, send_message_func):
        self.send_message = send_message_func

    # 사용가능 ticker 받아오기
    def update_all_tickers(self):
        self.all_tickers = pyupbit.get_tickers(fiat="KRW") # KRW로 거래되는 모든 티커를 가져옴

    # tickerData 클래스 생성
    def gen_tickers(self, ticker):
        # 문자열인 경우, 리스트로 변환
        if isinstance(ticker, str):
            ticker = [ticker]
        for symbol in ticker:
            setattr(self, symbol.lower(), tickerData())

    def con_tickers(self, ticker):
        delattr(self, ticker.lower())

    def get_upbit_api(self, ticker):
        while True:
            try:
                url = f"https://api.upbit.com/v1/candles/minutes/{getattr(self, ticker.lower()).candle}"
                querystring = {"market": ticker, "count": "500"}

                response = requests.request("GET", url, params=querystring)
                data = response.json()

                return data
            except Exception as e:
                logging.debug(e)

    #데이터프레임 변환
    def calc_df(self, df):
        df = df.reindex(index=df.index[::-1]).reset_index()
        df = df.rename(columns={'candle_date_time_kst': 'time', 'opening_price': 'open', 'high_price': 'high', 'low_price': 'low', 'trade_price': 'close', 'candle_acc_trade_price': 'volume'})
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        return df

    # RSI 계산하는 함수 정의
    def calculate_rsi(self, ticker):

        df = pd.DataFrame(self.get_upbit_api(ticker))
        last_bar = datetime.datetime.strptime(df['candle_date_time_kst'].iloc[0], '%Y-%m-%dT%H:%M:%S')

        with getattr(self, ticker.lower()).lock:
            getattr(self, ticker.lower()).last_row = df.tail(1)
            df = self.calc_df(df)
            df['rsi'] = trade_util.get_rsi(df.close, getattr(self, ticker.lower()).rsi_window)

            if getattr(self, ticker.lower()).last_bar == last_bar:
                #logging.info('pass')
                last_rsi = None
            elif getattr(self, ticker.lower()).last_bar is None:
                #logging.info('none')
                getattr(self, ticker.lower()).last_bar = last_bar
                getattr(self, ticker.lower()).ticker_df = df.iloc[:-1]
                last_rsi = df['rsi'].iloc[-1]
            else: 
                #logging.info('update')
                getattr(self, ticker.lower()).last_bar = last_bar
                getattr(self, ticker.lower()).ticker_df = pd.concat([getattr(self, ticker.lower()).ticker_df, df.iloc[-2:-1]])
                last_rsi = df['rsi'].iloc[-1]
        
        return last_rsi


    # RSI 알림을 보내는 함수 정의
    def send_rsi_alert(self, ticker):
        rsi = self.calculate_rsi(ticker)

        if rsi is not None:
            if rsi >= getattr(self, ticker.lower()).vol_high and getattr(self, ticker.lower()).wait is None:
                text = f"{ticker} : RSI {rsi}"
                getattr(self, ticker.lower()).wait = datetime.datetime.now().minute
                self.send_message(text)
                logging.info(text)

            if rsi <= getattr(self, ticker.lower()).vol_low and getattr(self, ticker.lower()).wait is None:
                text = f"{ticker} : RSI {rsi}"
                getattr(self, ticker.lower()).wait = datetime.datetime.now().minute
                self.send_message(text)
                logging.info(text)

        self.update_wait_dict()
        self.df_del_old()

        time.sleep(0.2)


    # 대기중인 티커를 업데이트하는 함수 정의
    def update_wait_dict(self):

        for ticker in self.tickers:
            temp = None
            with getattr(self, ticker.lower()).lock:
                if getattr(self, ticker.lower()).wait is not None:
                    value = getattr(self, ticker.lower()).wait
                    if datetime.datetime.now().minute >= value:
                        if datetime.datetime.now().minute - value < 10:
                            temp = value
                    else:
                        if datetime.datetime.now().minute + 60 - value < 10:
                            temp = value
                    getattr(self, ticker.lower()).wait = temp

    def df_del_old(self):    
        pass
            
    # 모든 티커에 대해 RSI 알림을 보내는 함수 정의
    def run(self):
        while True:
            for ticker in self.tickers:

                self.send_rsi_alert(ticker)

            time.sleep(60)