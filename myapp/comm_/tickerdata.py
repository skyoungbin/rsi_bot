import pandas as pd
import threading
import logging
import json

def save_on_change(func):
    def wrapper(self, *args, **kwargs):  # 가변 인자와 키워드 인자를 받을 수 있도록 수정
        func(self, *args, **kwargs)  # 원래의 메서드에 모든 인자 전달
        if self.manager:
            self.manager.save_tickers()  # 공통 후처리 로직
    return wrapper

class TickerData:

    def __init__(self, symbol):

        self.symbol = symbol
        self._ticker_df = pd.DataFrame()
        self._last_row = pd.DataFrame()
        self._last_bar = None
        self._candle = 30

        self._alarm = {}
        self._bot = {}

        self.lock = threading.Lock()

        self.manager = None

    def get_state(self):

        state = {}  
        state[self.__class__.__name__] = {
                "last_row": self.last_row.to_dict(orient='records'),
                "candle": self.candle,
        }

        alarm_items = self.alarm.items()
        for key, item in alarm_items:
            state[f'alarm-{key}'] = item.get_state()  # 각 Item의 상태를 가져옵니다.

        bot_items = self.bot.items()
        for key, item in bot_items:
            state[f'bot-{key}'] = item.get_state() 

        return state


    def reset_params(self):
        self.ticker_df = pd.DataFrame()
        self.last_row = pd.DataFrame()
        self.last_bar = None

    def update_tickers_params(self, params, value):

        if params in ['candle']:
            setattr(self, params, value)
            if params in ['candle']:
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

    def get_ticker_df(self):
        with self.lock:
            tmp_df = self._ticker_df.copy()

        alarm_list = self.get_alarm_key()
        logging.info(alarm_list)

        for alarm_name in alarm_list:
            alarm = self.get_alarm_item(alarm_name)
            logging.info(alarm)
            tmp_df = pd.concat([tmp_df, alarm.df], axis=1, join='outer')

        logging.info(tmp_df)
        return tmp_df


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
    def candle(self):
        with self.lock:
            return self._candle

    @candle.setter
    @save_on_change
    def candle(self, value):
        valid_values = [1, 3, 5, 15, 10, 30, 60, 240]
        if value not in valid_values:
            raise ValueError("분 단위. 가능한 값 : 1, 3, 5, 15, 10, 30, 60, 240")
        with self.lock:
            self._candle = value


    @property
    def alarm(self):
        with self.lock:  
            return self._alarm

    @save_on_change
    def add_alarm_key(self, key, item):
        with self.lock:  
            self._alarm[key] = item

    def get_alarm_key(self):
        with self.lock: 
            return list(self._alarm.keys())

    @save_on_change
    def delete_alarm_key(self, key):
        with self.lock:  
            if key in self._alarm:
                del self._alarm[key]

    def get_alarm_item(self, key):
        with self.lock:  
            return self._alarm.get(key)
    
    @save_on_change
    def update_alarm_item(self, key, **kwargs):

        item = self.get_alarm_item(key)
        with self.lock:  
            if item is not None:
                for attr_name, attr_value in kwargs.items():
                    setattr(item, attr_name, attr_value)



    @property
    def bot(self):
        with self.lock:  
            return self._bot

    @save_on_change
    def add_bot_key(self, key, item):
        with self.lock:  
            self._bot[key] = item

    def get_bot_key(self):
        with self.lock: 
            return list(self._bot.keys())

    @save_on_change
    def delete_bot_key(self, key):
        with self.lock:  
            if key in self._bot:
                del self._bot[key]

    def get_bot_item(self, key):
        with self.lock:  
            return self._bot.get(key)
    
    @save_on_change
    def update_bot_item(self, key, **kwargs):

        item = self.get_bot_item(key)
        with self.lock:  
            if item is not None:
                for attr_name, attr_value in kwargs.items():
                    setattr(item, attr_name, attr_value)


    # @property
    # def bot(self):
    #     with self.lock:
    #         return self._bot

    # def add_bot_list(self, value):
    #     self._bot.append(value)

    # def remove_bot_list(self, value):
    #     if value in self._bot:
    #         self._bot.remove(value)


    def __getstate__(self):
        state = self.__dict__.copy()

        del state['_ticker_df']
        del state['_last_row']
        del state['_last_bar']
        del state['lock']

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        self._ticker_df = pd.DataFrame()
        self._last_row = pd.DataFrame()
        self._last_bar = None
        self.lock = threading.Lock()
