import pandas as pd
import time 
import logging
import numpy as np
import pyupbit
import json
import copy

import comm_.trade_util as trade_util
import comm_.tool_util as tool_util

class Bot():

    def __init__(self, tickerdata):

        self.symbol = copy.deepcopy(tickerdata.symbol)
        self.candle = tickerdata.candle

        self.df = pd.DataFrame()
        self.orderbook = pd.DataFrame()

        self.trade_price = None
        self.purchase_status = False

        self.degree = 40
        self.degree_threshold = np.tan(np.radians(self.degree))

        self.days_ago = 90
        self.total_assets = 100000

        self.get_upbit_api()

    def get_upbit_api(self):
        self.df = pyupbit.get_ohlcv(self.symbol, interval=f'minute{self.candle}', count=trade_util.calculate_count_from_days_ago(self.candle, self.days_ago))
        self.df = self.df.iloc[:-1]
        self.df = self.position_df(self.df)

    def position_df(self, df):
        
        # rsi 계산
        df['rsi'] = trade_util.get_rsi(df.close, 14)

        # 이평선 계산 (예: 20기간 단순 이동 평균)
        df['SMA'] = df['close'].rolling(window=20).mean()

        # 이평선 기울기 계산
        df['SMA_slope'] = np.arctan(df['SMA'].diff() / 1)  # 1은 한 봉 간격. 실제 거리는 중요하지 않으므로 1로 가정

        # 거래량 급등 여부 확인 (예: 이전 봉 대비 2배 증가)
        df['volume_spike'] = df['volume'] > (df['volume'].shift(1) * 2)


        df["position"] = np.where(df['rsi'] < 30, 0, np.nan) # sell 조건
        df["position"] = np.where((df['SMA_slope'] >= self.degree_threshold) & df['volume_spike'], 1, df.position) # buy조건
        df["position"] = df.position.ffill().fillna(0) 

        return df


    # 계산하는 함수 정의
    def calc(self, tick_stat, df):

        df = self.position_df(df)

        if tick_stat == 'pass':
            pass
        elif tick_stat == 'none':
            self.get_upbit_api()
        else: 
            self.df = pd.concat([self.df, df.iloc[-2:-1]])
            self.df = self.df.iloc[1:]

        return self.df.iloc[-1]["position"]


    # 알림을 보내는 함수 정의
    def trade(self, tick_stat, df):

        self.trade_price = df.iloc[-1]['close']
        
        signal = self.calc(tick_stat, df)
        text = ''

        if signal == 1: 
            if self.purchase_status == False:

                data, updated_orderbook, purchase_status, updated_total_assets = trade_util.buy_order(
                    self.orderbook, self.total_assets, self.symbol, self.trade_price
                )
                self.orderbook = updated_orderbook
                self.purchase_status = purchase_status
                self.total_assets = updated_total_assets

                text = {}
                text[self.symbol] = data
                text = json.dumps(text)

        elif signal == 0:
            if self.purchase_status == True:

                data, updated_orderbook, purchase_status, updated_total_assets = trade_util.sell_order(
                    self.orderbook, self.total_assets, self.symbol, self.trade_price
                )
                self.orderbook = updated_orderbook
                self.purchase_status = purchase_status
                self.total_assets = updated_total_assets
                
                text = {}
                text[self.symbol] = data
                text = json.dumps(text)

        if text:
            return True, text  
        else:
            return False, "" 


    def get_state(self):

        return {
                "last_row": self.orderbook.tail(1).to_dict(orient='records'),
                "total_assets": self.total_assets,
                "purchase_status": self.purchase_status,
                "return_rate": trade_util.calculate_return(self.orderbook.iloc[-1]['price'], self.trade_price) * 100 if self.purchase_status else None
            }


    def __getstate__(self):
        state = self.__dict__.copy()

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)


