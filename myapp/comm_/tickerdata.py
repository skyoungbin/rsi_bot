import pandas as pd
import threading
import logging

class tickerData:
    def __init__(self):

        self._ticker_df = pd.DataFrame()
        self._last_row = pd.DataFrame()
        self._last_bar = None
        self._wait_msg = None
        self._last_rsi = None
        self._candle = 1
        self._vol_high = 70
        self._vol_low = 40
        self._rsi_window = 14

        self._timer = None
        self.lock = threading.Lock()

    def get_state(self):

        return {
            self.__class__.__name__: {
                "last_row": self.last_row.to_dict(orient='records'),
                "last_rsi": self.last_rsi,
                "candle": self.candle,
                "vol_high": self.vol_high,
                "vol_low": self.vol_low,
                "rsi_window": self.rsi_window,
            }
        }
    
    def set_wait(self, value):
        logging.debug('start set_wait')

        self.wait_msg = value

        if self.timer is None:
            #self.timer.cancel()  # 이미 실행 중인 타이머가 있다면 취소합니다.
            self.timer = threading.Timer(300, self.reset_wait)  # 10분 후에 reset_wait 호출
            self.timer.start()

    def reset_wait(self):
        logging.debug('start reset_wait')

        self.wait_msg = None
        self.timer = None

    def reset_params(self):
        self.ticker_df = pd.DataFrame()
        self.last_row = pd.DataFrame()
        self.last_bar = None
        self.wait_msg = None
        self.last_rsi = None
        self.timer = None

    def update_tickers_params(self, params, value):

        if params in ['candle', 'vol_high', 'vol_low', 'rsi_window']:
            setattr(self, params, value)
            if params in ['candle', 'rsi_window']:
                self.reset_params()
        else:
            raise ValueError("알 수 없는 params 값 입니다")


    @property
    def ticker_df(self):
        with self.lock:
            return self._ticker_df

    @ticker_df.setter
    def ticker_df(self, value):
        with self.lock:
            self._ticker_df = value

    @property
    def last_row(self):
        with self.lock:
            return self._last_row

    @last_row.setter
    def last_row(self, value):
        with self.lock:
            self._last_row = value

    @property
    def last_row(self):
        with self.lock:
            return self._last_row

    @last_row.setter
    def last_row(self, value):
        with self.lock:
            self._last_row = value

    @property
    def last_bar(self):
        with self.lock:
            return self._last_bar

    @last_bar.setter
    def last_bar(self, value):
        with self.lock:
            self._last_bar = value

    @property
    def wait_msg(self):
        with self.lock:
            return self._wait_msg

    @wait_msg.setter
    def wait_msg(self, value):
        with self.lock:
            self._wait_msg = value

    @property
    def last_rsi(self):
        with self.lock:
            return self._last_rsi

    @last_rsi.setter
    def last_rsi(self, value):
        with self.lock:
            self._last_rsi = value

    @property
    def candle(self):
        with self.lock:
            return self._candle

    @candle.setter
    def candle(self, value):
        valid_values = [5, 15, 10, 30, 60, 240]
        if value not in valid_values:
            raise ValueError("분 단위. 가능한 값 : 5, 15, 10, 30, 60, 240")
        with self.lock:
            self._candle = value

    @property
    def vol_high(self):
        with self.lock:
            return self._vol_high

    @vol_high.setter
    def vol_high(self, value):
        if not (1 <= value <= 100) or value < self.vol_low:
            raise ValueError("Value 1 ~ 100사이의 값 vol_low 보다 높아야 함.")
        with self.lock:
            self._vol_high = value

    @property
    def vol_low(self):
        with self.lock:
            return self._vol_low

    @vol_low.setter
    def vol_low(self, value):
        if not (1 <= value <= 100) or value > self.vol_high:
            raise ValueError("Value 1 ~ 100사이의 값 vol_high 보다 낮아야 함.")
        with self.lock:
            self._vol_low = value

    @property
    def rsi_window(self):
        with self.lock:
            return self._rsi_window

    @rsi_window.setter
    def rsi_window(self, value):
        if not (1 <= value <= 25):
            raise ValueError("Value 1 ~ 25사이의 값")
        with self.lock:
            self._rsi_window = value

    @property
    def timer(self):
        with self.lock:
            return self._timer

    @timer.setter
    def timer(self, value):
        with self.lock:
            self._timer = value