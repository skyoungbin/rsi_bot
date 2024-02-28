import requests
import pandas as pd
import time
import pyupbit
import telegram
import datetime
import numpy as np
import asyncio
import telegram as tel
import os
# RSI 알림 클래스 정의
class RsiNotifier:
    def __init__(self, token, chat_id):
        self.bot = tel.Bot(token=token)
        self.chat_id = chat_id
        self.wait_dict = {}  # 알림을 보낸 티커 대기 시간 저장
        self.tickers = pyupbit.get_tickers(fiat="KRW")  # KRW로 거래되는 모든 티커를 가져옴

    # 메세지를 보내는 함수 정의 
    async def send_msg(self, msg):
        await self.bot.sendMessage(chat_id=self.chat_id, text=msg) 

    # RSI 계산하는 함수 정의
    def calculate_rsi(self, symbol):
        url = "https://api.upbit.com/v1/candles/minutes/30"
        querystring = {"market": symbol, "count": "500"}

        response = requests.request("GET", url, params=querystring)
        data = response.json()
        df = pd.DataFrame(data)

        df = df.reindex(index=df.index[::-1]).reset_index()
        df['close'] = df["trade_price"]

        def rsi(ohlc: pd.DataFrame, period: int = 14):
            ohlc["close"] = ohlc["close"]
            delta = ohlc["close"].diff()

            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0

            _gain = up.ewm(com=(period - 1), min_periods=period).mean()
            _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()

            RS = _gain / _loss
            return pd.Series(100 - (100 / (1 + RS)), name="RSI")

        return rsi(df, 14).iloc[-1]

    # RSI 알림을 보내는 함수 정의
    def send_rsi_alert(self, ticker):
        rsi = self.calculate_rsi(ticker)

        if rsi >= 71 and ticker not in self.wait_dict:
            text = f"{ticker} : RSI {round(rsi)}"
            asyncio.run(self.send_msg(text))
            self.wait_dict[ticker] = datetime.datetime.now().minute
            print(text)

        if rsi <= 40 and ticker not in self.wait_dict:
            text = f"{ticker} : RSI {round(rsi)}"
            asyncio.run(self.send_msg(text))
            self.wait_dict[ticker] = datetime.datetime.now().minute
            print(text)

        self.update_wait_dict()

        time.sleep(0.1)

    # 대기중인 티커를 업데이트하는 함수 정의
    def update_wait_dict(self):
        temp_dict = {}
        for key, value in self.wait_dict.items():
            if datetime.datetime.now().minute >= value:
                if datetime.datetime.now().minute - value < 5:
                    temp_dict[key] = value
            else:
                if datetime.datetime.now().minute + 60 - value < 5:
                    temp_dict[key] = value
        self.wait_dict = temp_dict
        

    # 모든 티커에 대해 RSI 알림을 보내는 함수 정의
    def run(self):
        while True:
            for ticker in self.tickers:
                try:
                    self.send_rsi_alert(ticker)
                except:
                    continue

if __name__ == "__main__":
    tocken=os.getenv('TOCKEN')
    chat_id=os.getenv('CHAT_ID')
    notifier = RsiNotifier(tocken, chat_id)
    notifier.run()
