import threading
import pandas as pd
import logging

import comm_.tool_util as tool_util
import comm_.trade_util as trade_util


def save_on_change(func):
    def wrapper(self, value):
        func(self, value)  # 원래의 setter 실행
        if self.manager:
            self.manager.save_users()  # 공통 후처리 로직
    return wrapper

class UserData:
    def __init__(self):

        self._purchase_status = False
        self._total_assets = 10000
        self._neutral_price = 0
        self._buy_ticker = None
        self._orderbook = pd.DataFrame()

        self.lock = threading.Lock()

    def get_state(self, trade_price):
        return {
            "last_row": self.orderbook.tail(1).to_dict(orient='records'),
            "total_assets": self.total_assets,
            "purchase_status": self.purchase_status,
            "buy_ticker": self.buy_ticker,
            "return_rate": trade_util.calculate_return(self.orderbook.iloc[-1]['price'], trade_price) * 100 if self.purchase_status else None
        }

    def buy_order(self, ticker, trade_price):

        data, updated_orderbook, purchase_status, updated_total_assets = trade_util.buy_order(
            self.orderbook, self.total_assets, ticker, trade_price
        )
        self.orderbook = updated_orderbook
        self.purchase_status = purchase_status
        self.total_assets = updated_total_assets

        return data

    def sell_order(self, ticker, trade_price):

        data, updated_orderbook, purchase_status, updated_total_assets = trade_util.sell_order(
            self.orderbook, self.total_assets, ticker, trade_price
        )
        self.orderbook = updated_orderbook
        self.purchase_status = purchase_status
        self.total_assets = updated_total_assets

        return data

    @property
    def purchase_status(self):
        with self.lock:
            return self._purchase_status

    @purchase_status.setter
    @save_on_change
    def purchase_status(self, value):
        with self.lock:
            self._purchase_status = value

    @property
    def total_assets(self):
        with self.lock:
            return self._total_assets

    @total_assets.setter
    @save_on_change
    def total_assets(self, value):
        with self.lock:
            self._total_assets = value

    @property
    def long_price(self):
        with self.lock:
            return self._long_price

    @long_price.setter
    @save_on_change
    def long_price(self, value):
        with self.lock:
            self._long_price = value

    @property
    def neutral_price(self):
        with self.lock:
            return self._neutral_price

    @neutral_price.setter
    @save_on_change
    def neutral_price(self, value):
        with self.lock:
            self._neutral_price = value

    @property
    def buy_ticker(self):
        with self.lock:
            return self._buy_ticker

    @buy_ticker.setter
    @save_on_change
    def buy_ticker(self, value):
        with self.lock:
            self._buy_ticker = value

    @property
    def orderbook(self):
        with self.lock:
            return self._orderbook

    @orderbook.setter
    def orderbook(self, value):
        with self.lock:
            self._orderbook = value



    # def __getstate__(self):
    #     state = self.__dict__.copy()

    #     del state['_orderbook']
    #     del state['lock']

    #     return state

    # def __setstate__(self, state):

    #     self.__dict__.update(state)

    #     self._orderbook = pd.DataFrame()
    #     self.lock = threading.Lock()


    def to_dict(self):
        try:
            return {
                'purchase_status': self._purchase_status,
                'total_assets': self._total_assets,
                'neutral_price': self._neutral_price,
                'buy_ticker': self._buy_ticker,
                'orderbook': self._orderbook.to_dict(orient='records')
            }
        except Exception as e:
            logging.error(f"Failed to save tickers: {e}")

    @classmethod
    def from_dict(cls, data):
        try:
            user = cls()
            user._purchase_status = data['purchase_status']
            user._total_assets = data['total_assets']
            user._neutral_price = data['neutral_price']
            user._buy_ticker = data['buy_ticker']
            user._orderbook = pd.DataFrame(data['orderbook'])
            return user
        except Exception as e:
            logging.error(f"Failed to save tickers: {e}")