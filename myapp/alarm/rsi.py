import pandas as pd
import time 
import logging
import copy

import comm_.trade_util as trade_util
import comm_.tool_util as tool_util
from comm_.alarm_wait import AlarmWait

class Alarm(AlarmWait):


    def __init__(self, tickerdata):
        super().__init__()

        self.symbol = copy.deepcopy(tickerdata.symbol)

        self.df = pd.DataFrame()
        self.tick_df = pd.DataFrame()
        self.last_rsi = None
        self._vol_high = 70
        self._vol_low = 40
        self._rsi_window = 14


    # 계산하는 함수 정의
    def calc(self, df, tick_stat):

        df['rsi'] = trade_util.get_rsi(df.close, self.rsi_window)
        self.tick_df = pd.concat([self.tick_df, df[['timestamp', 'rsi']].tail(1)])

        if tick_stat == 'pass':
            pass
        elif tick_stat == 'none':
            self.df = df.iloc[:-1].dropna()['rsi']
            self.tick_df = pd.DataFrame()
        else: 
            self.df = pd.concat([self.df, df.iloc[-2:-1]['rsi']])

        self.last_rsi = df['rsi'].iloc[-1]
        
        return self.last_rsi


    # 알림을 보내는 함수 정의
    def alert(self, df, tick_stat):
        
        rsi = self.calc(df, tick_stat)
        text = ''

        if rsi is not None:

            if (
                rsi >= self.vol_high
                or
                rsi <= self.vol_low
                ):
                if self.wait_msg is None:

                    text = f"{self.symbol} : RSI {rsi}"

                    logging.info(text)
                else:
                    pass

                self.set_wait(tool_util.get_kr_time())

        time.sleep(0.2)

        if text:
            return True, text  
        else:
            return False, "" 


    def get_state(self):

        return {
                "last_rsi": self.last_rsi,
                "vol_high": self._vol_high,
                "vol_low": self._vol_low,
                "rsi_window": self._rsi_window,
            }


    @property
    def vol_high(self):
        return self._vol_high

    @vol_high.setter
    def vol_high(self, value):
        if not (1 <= value <= 100) or value < self.vol_low:
            raise ValueError("Value 1 ~ 100사이의 값 vol_low 보다 높아야 함.")
        self._vol_high = value

    @property
    def vol_low(self):
        return self._vol_low

    @vol_low.setter
    def vol_low(self, value):
        if not (1 <= value <= 100) or value > self.vol_high:
            raise ValueError("Value 1 ~ 100사이의 값 vol_high 보다 낮아야 함.")
        self._vol_low = value

    @property
    def rsi_window(self):
        return self._rsi_window

    @rsi_window.setter
    def rsi_window(self, value):
        try:
            value = int(value)  # 문자열을 정수로 변환 시도
        except ValueError:
            # 변환 실패 시, 적절한 예외 처리
            raise ValueError("rsi_window must be a number or a numeric string.")

        if not (1 <= value <= 25):
            raise ValueError("Value 1 ~ 25사이의 값")

        self._rsi_window = value

    def __getstate__(self):
        state = self.__dict__.copy()

        del state['df']
        del state['tick_df']
        del state['last_rsi']

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        self.df = pd.DataFrame()
        self.tick_df = pd.DataFrame()
        self.last_rsi = None


