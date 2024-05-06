import dill as pickle
import threading
import pyupbit
#import comm_.tickerdata as tickerdata
from comm_.tickerdata import TickerData
import comm_.tool_util as tool_util



class TickerManger:

    def __init__(self):

        self._all_tickers = []
        self._tickers = {}

        self.all_tickers_lock = threading.Lock()
        self.tickers_lock = threading.Lock()

        self.update_all_tickers()


    # 사용가능 ticker 받아오기
    def update_all_tickers(self):
        with self.all_tickers_lock:
            self._all_tickers = pyupbit.get_tickers(fiat="KRW")  # KRW로 거래되는 모든 티커를 가져옴
        self.save_tickers()

    def schedule_update_all_tickers(self):
        # Timer를 생성하고 시작합니다.
        t = threading.Timer(tool_util.delay_every_6h(), self.schedule_update_all_tickers)
        t.start()

        self.update_all_tickers()

    def save_tickers(self):
        with open('./data_/tickers.pkl', 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_tickers(cls):
        with open('./data_/tickers.pkl', 'rb') as f:
            manager = pickle.load(f)
        return manager

    def __getstate__(self):
        state = self.__dict__.copy()

        del state['all_tickers_lock']
        del state['tickers_lock']

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        self.all_tickers_lock = threading.Lock()
        self.tickers_lock = threading.Lock()

    @property
    def tickers(self):
        with self.tickers_lock:
            return self._tickers

    def gen_tickers(self, ticker_symbols):
        if isinstance(ticker_symbols, str):
            ticker_symbols = [ticker_symbols]
        for symbol in ticker_symbols:
            if symbol.lower() not in self.tickers:
                ticker = TickerData(symbol.upper())
                ticker.manager = self
                self.tickers[symbol.lower()] = ticker
        self.save_tickers()
    
    def con_tickers(self, ticker_symbol):
        symbol = ticker_symbol.lower()
        if symbol in self.tickers:
            del self.tickers[symbol]
        self.save_tickers()

    @property
    def all_tickers(self):
        with self.all_tickers_lock:
            return self._all_tickers

    # @property
    # def tickers(self):
    #     with self.lock:
    #         return self._tickers

    # @tickers.setter
    # def tickers(self, value):
    #     with self.lock:
    #         self._tickers = value