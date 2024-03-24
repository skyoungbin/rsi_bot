import threading
import pandas as pd

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
        self._long_price = 0
        self._neutral_price = 0
        self._buy_ticker = None
        self._orderbook = pd.DataFrame()

        self.lock = threading.Lock()

    def get_state(self, trade_price):

        return {
            self.__class__.__name__: {
                "last_row": self.orderbook.tail(1).to_dict(orient='records'),
                "total_assets": self.total_assets,
                "purchase_status": self.purchase_status,
                "buy_ticker": self.buy_ticker,
                "return_rate": trade_util.calculate_return(self.long_price, trade_price) * 100 if self.buy_ticker else None
            }
        }

    def buy_order(self, ticker, trade_price):
        self.buy_ticker = ticker
        self.long_price = trade_price
        total_assets = self.total_assets

        data = {
            "trade_time": [tool_util.get_kr_time().isoformat()],  # 실제 trade_time 값을 사용하십시오
            "ticker": [self.buy_ticker],
            "price": [self.long_price],
            "position": ['long'],
            "total_assets": [total_assets],
            "return_rate": ['']
        }

        # 데이터프레임 생성
        orderbook = pd.DataFrame(data).set_index('trade_time')
        self.orderbook = pd.concat([self.orderbook, orderbook])
        #orderbook.set_index('trade_time', inplace=True)

        self.purchase_status = True

        return data

    def sell_order(self, ticker, trade_price):
        self.neutral_price = trade_price
        return_rate = trade_util.calculate_return(self.long_price, self.neutral_price)
        self.total_assets = self.total_assets + trade_util.calculate_profit(return_rate, self.total_assets)

        data = {
            "trade_time": [tool_util.get_kr_time().isoformat()],  # 실제 trade_time 값을 사용하십시오
            "ticker": [ticker],
            "price": [self.neutral_price],
            "position": ['neutral'],
            "total_assets": [self.total_assets],
            "return_rate": [return_rate * 100]
        }

        # 데이터프레임 생성
        orderbook = pd.DataFrame(data).set_index('trade_time')
        self.orderbook = pd.concat([self.orderbook, orderbook])
        #orderbook.set_index('trade_time', inplace=True)

        self.purchase_status = False
        self.buy_ticker = None

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



    def __getstate__(self):
        state = self.__dict__.copy()

        del state['_orderbook']
        del state['lock']

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        self._orderbook = pd.DataFrame()
        self.lock = threading.Lock()