import threading
import logging
import pyupbit

import comm_.tool_util as tool_util

class alltickerData:
    def __init__(self):

        self._all_tickers = []
        self._tickers = ['KRW-BTC']

        self.all_tickers_lock = threading.Lock()
        self.tickers_lock = threading.Lock()

        self.update_all_tickers()

    @property
    def tickers(self):
        with self.tickers_lock:
            return self._tickers

    def append_tickers(self, item):
        with self.tickers_lock:
            self._tickers.append(item)
    
    def remove_tickers(self, item):
        with self.tickers_lock:
            self._tickers.remove(item)

    @property
    def all_tickers(self):
        with self.all_tickers_lock:
            return self._all_tickers

    # 사용가능 ticker 받아오기
    def update_all_tickers(self):
        with self.all_tickers_lock:
            self._all_tickers = pyupbit.get_tickers(fiat="KRW")  # KRW로 거래되는 모든 티커를 가져옴

    def schedule_update_all_tickers(self):
        # Timer를 생성하고 시작합니다.
        t = threading.Timer(tool_util.delay_every_6h(), self.schedule_update_all_tickers)
        t.start()

        self.update_all_tickers()