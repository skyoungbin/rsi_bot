import threading
import logging
import pyupbit
import pickle

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
        self.save()
    
    def remove_tickers(self, item):
        with self.tickers_lock:
            self._tickers.remove(item)
        self.save()

    @property
    def all_tickers(self):
        with self.all_tickers_lock:
            return self._all_tickers

    # 사용가능 ticker 받아오기
    def update_all_tickers(self):
        with self.all_tickers_lock:
            self._all_tickers = pyupbit.get_tickers(fiat="KRW")  # KRW로 거래되는 모든 티커를 가져옴
        self.save()

    def schedule_update_all_tickers(self):
        # Timer를 생성하고 시작합니다.
        t = threading.Timer(tool_util.delay_every_6h(), self.schedule_update_all_tickers)
        t.start()

        self.update_all_tickers()

    def __getstate__(self):
        state = self.__dict__.copy()

        del state['all_tickers_lock']
        del state['tickers_lock']


        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        self.all_tickers_lock = threading.Lock()
        self.tickers_lock = threading.Lock()

    def save(self):
        with open('./data_/alltickerdata.pkl', 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls):
        with open('./data_/alltickerdata.pkl', 'rb') as f:
            allticker_data = pickle.load(f)
        return allticker_data