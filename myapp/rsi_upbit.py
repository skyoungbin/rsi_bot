import requests
import pandas as pd
import time
import datetime
import logging
import threading
import json

import comm_.trade_util as trade_util
import comm_.tool_util as tool_util
import comm_.alltickerdata as alltickerdata
import comm_.tickerdata as tickerdata
import comm_.userdata as userdata

# RSI 알림 클래스 정의
class RsiNotifier:
    def __init__(self):

        self.alltickerdata = alltickerdata.alltickerData()

        self.userdata = userdata.userData(self)

        self.gen_tickers(self.alltickerdata.tickers)

    
    # slack 메세지
    def set_slack(self, send_message_func, send_pinned_func):
        self.send_message = send_message_func
        self.pinned_message = send_pinned_func

    def set_schedule(self):
        self.schedule_del_olddf()
        self.schedule_report_pinned_message()


    # tickerData 클래스 생성
    def gen_tickers(self, ticker):
        # 문자열인 경우, 리스트로 변환
        if isinstance(ticker, str):
            ticker = [ticker]
        for symbol in ticker:
            setattr(self, symbol.lower(), tickerdata.tickerData())

    # tickerData 클래스 제거
    def con_tickers(self, ticker):
        delattr(self, ticker.lower())

    def get_upbit_api(self, ticker):
        logging.debug('start get_upbit_api')
        while True:
            try:
                url = f"https://api.upbit.com/v1/candles/minutes/{getattr(self, ticker.lower()).candle}"
                querystring = {"market": ticker, "count": "500"}

                response = requests.request("GET", url, params=querystring)
                data = response.json()

                return pd.DataFrame(data)
            except Exception as e:
                logging.debug(e)

    def update_last_row(self, ticker, df):
        logging.debug('start update_last_row')

        getattr(self, ticker.lower()).last_row = df.head(1)

    # 데이터프레임 변환
    def calc_df(self, df):
        df = df.reindex(index=df.index[::-1]).reset_index()
        df = df.rename(columns={
            'candle_date_time_kst': 'time',
            'opening_price': 'open',
            'high_price': 'high',
            'low_price': 'low',
            'trade_price': 'close',
            'candle_acc_trade_price': 'volume',
            })
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        return df

    # RSI 계산하는 함수 정의
    def calculate_rsi(self, ticker):
        logging.debug('start calculate_rsi')

        df = self.get_upbit_api(ticker)
        last_bar = datetime.datetime.strptime(df['candle_date_time_kst'].iloc[0], '%Y-%m-%dT%H:%M:%S')
        self.update_last_row(ticker, df)


        df = self.calc_df(df)
        df['rsi'] = trade_util.get_rsi(df.close, getattr(self, ticker.lower()).rsi_window)

        if getattr(self, ticker.lower()).last_bar == last_bar:
            #logging.info('pass')
            last_rsi = df['rsi'].iloc[-1]
        elif getattr(self, ticker.lower()).last_bar is None:
            #logging.info('none')
            getattr(self, ticker.lower()).last_bar = last_bar
            getattr(self, ticker.lower()).ticker_df = df.iloc[:-1].dropna()
            last_rsi = df['rsi'].iloc[-1]
        else: 
            #logging.info('update')
            getattr(self, ticker.lower()).last_bar = last_bar
            getattr(self, ticker.lower()).ticker_df = pd.concat([getattr(self, ticker.lower()).ticker_df, df.iloc[-2:-1]])
            last_rsi = df['rsi'].iloc[-1]
        getattr(self, ticker.lower()).last_rsi = last_rsi
        
        return last_rsi


    # RSI 알림을 보내는 함수 정의
    def send_rsi_alert(self, ticker):
        
        rsi = self.calculate_rsi(ticker)
        #logging.info(rsi)

        if rsi is not None:

            if (
                rsi >= getattr(self, ticker.lower()).vol_high
                or
                rsi <= getattr(self, ticker.lower()).vol_low
                ):
                if getattr(self, ticker.lower()).wait_msg is None:

                    text = f"{ticker} : RSI {rsi}"

                    self.send_message(text)
                    logging.info(text)
                else:
                    pass

                getattr(self, ticker.lower()).set_wait(tool_util.get_kr_time())

        time.sleep(0.2)
    
    def del_olddf(self): 
        logging.debug('start del_olddf')
        tickers = self.alltickerdata.tickers
        for ticker in tickers:
            getattr(self, ticker.lower()).ticker_df = getattr(self, ticker.lower()).ticker_df[getattr(self, ticker.lower()).ticker_df.index > tool_util.one_week_ago()]

    def schedule_del_olddf(self):
        # Timer를 생성하고 시작합니다.
        t = threading.Timer(tool_util.delay_h(6), self.schedule_del_olddf)
        t.start()

        self.del_olddf()

    def report_pinned_message(self):
        logging.debug('start report_pinned_message')
 
        message = f'''
        감시중인 Ticker = {self.alltickerdata.tickers}
        {json.dumps(self.userdata.get_state(), indent=4)}
        '''

        self.pinned_message(message)

    def schedule_report_pinned_message(self):
        # Timer를 생성하고 시작합니다.
        t = threading.Timer(tool_util.delay_h(8), self.schedule_report_pinned_message)
        t.start()

        self.report_pinned_message()
            
    # 모든 티커에 대해 RSI 알림을 보내는 함수 정의
    def run(self):
        while True:
            tickers = self.alltickerdata.tickers
            for ticker in tickers:

                self.send_rsi_alert(ticker)

            time.sleep(tool_util.delay_s(20))