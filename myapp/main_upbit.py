import requests
import pandas as pd
import time
import datetime
import logging
import threading
import json
import os
from dateutil import tz
from concurrent.futures import ThreadPoolExecutor, wait

import comm_.trade_util as trade_util
import comm_.tool_util as tool_util
#import comm_.alltickerdata as alltickerdata
#import comm_.tickerdata as tickerdata
#import comm_.tickermanager as tickermanager
#import comm_.userdata as userdata
#import comm_.usermanager as usermanager

from comm_.tickermanager import TickerManager
from comm_.usermanager import UserManager

# RSI 알림 클래스 정의
class Notifier:

    def __init__(self, event_manager):

        self.event_manager = event_manager

        #self.alltickerdata = alltickerdata.alltickerData()
        #self.tickermanager = tickermanager.TickerManger()
        #self.usermanager = usermanager.UserManger()

        self.alarm_instances = tool_util.load_alarm_instances('./alarm')
        self.bot_instances = tool_util.load_bot_instances('./bot')


        if os.path.exists('./data_/tickers.pkl') and os.path.exists('./data_/users.pkl'):
            logging.info('저장된 파일을 불러옵니다.')
            self.tickermanager = TickerManager.load_tickers(self.alarm_instances, self.bot_instances)
            self.usermanager = UserManager.load_users()
        else:
            
            logging.info('초기 세팅으로 시작합니다.')
            self.tickermanager = TickerManager()
            self.usermanager = UserManager()

            ticker = 'KRW-BTC'
            self.tickermanager.gen_tickers(ticker)
            alarm_class = self.alarm_instances['rsi'](self.tickermanager.tickers[ticker])
            self.tickermanager.tickers[ticker].add_alarm_key('rsi', alarm_class)
            self.usermanager.gen_users('default')


        self.set_schedule()
  
  
    # slack 메세지

    def send_message(self, message):
        self.event_manager.publish('send_message', message)

    def pinned_message(self, message):
        self.event_manager.publish('pinned_message', message)

    def set_schedule(self):
        self.schedule_del_olddf()
        #self.schedule_report_pinned_message()


    def get_upbit_api(self, ticker):
        logging.debug('start get_upbit_api')
        while True:
            try:
                url = f"https://api.upbit.com/v1/candles/minutes/{self.tickermanager.tickers[ticker].candle}"
                querystring = {"market": ticker, "count": "500"}

                response = requests.request("GET", url, params=querystring)
                data = response.json()

                return pd.DataFrame(data)
            except Exception as e:
                logging.debug(e)

    def update_last_row(self, ticker, df):
        logging.debug('start update_last_row')

        self.tickermanager.tickers[ticker].last_row = df.head(1)


    # tick 계산하는 함수 정의
    def calculate_tick(self, ticker):
        logging.debug('start calculate_rsi')

        df = self.get_upbit_api(ticker)
        last_bar = datetime.datetime.strptime(df['candle_date_time_kst'].iloc[0], '%Y-%m-%dT%H:%M:%S')
        self.update_last_row(ticker, df)

        df = trade_util.calc_df(df)

        if self.tickermanager.tickers[ticker].last_bar == last_bar:
            tick_stat = 'pass'
        elif self.tickermanager.tickers[ticker].last_bar is None:
            tick_stat = 'none'
            self.tickermanager.tickers[ticker].last_bar = last_bar
            self.tickermanager.tickers[ticker].ticker_df = df.iloc[:-1].dropna()
        else: 
            tick_stat = 'update'
            self.tickermanager.tickers[ticker].last_bar = last_bar
            self.tickermanager.tickers[ticker].ticker_df = pd.concat([self.tickermanager.tickers[ticker].ticker_df, df.iloc[-2:-1]])

        self.process_alarm(tick_stat, ticker, df)
        self.process_bot(tick_stat, ticker, df)


    def process_alarm(self, tick_stat, ticker, df):
        alarm_list = self.tickermanager.tickers[ticker].get_alarm_key()
        for alarm_name in alarm_list:
            try:
                alarm = self.tickermanager.tickers[ticker].get_alarm_item(alarm_name)
                result, text = alarm.alert(df, tick_stat)
                
                if result:
                    self.send_message(text)
            except Exception as e:
                logging.error(f"에러발생: {e}")

    def process_bot(self, tick_stat, ticker, df):
        bot_list = self.tickermanager.tickers[ticker].get_bot_key()
        for bot_name in bot_list:
            try:
                bot = self.tickermanager.tickers[ticker].get_bot_item(bot_name)
                result, text = bot.trade(tick_stat, df)
                
                if result:
                    self.send_message(text)
            except Exception as e:
                logging.error(f"에러발생: {e}")

    def del_olddf(self): 
        logging.debug('start del_olddf')
        tickers = list(self.tickermanager.tickers.keys()) 
        for ticker in tickers:
            self.tickermanager.tickers[ticker].ticker_df = self.tickermanager.tickers[ticker].ticker_df[self.tickermanager.tickers[ticker].ticker_df.index > tool_util.one_week_ago()]
            alarm_list = self.tickermanager.tickers[ticker].get_alarm_key()
            for alarm_name in alarm_list:
                alarm = self.tickermanager.tickers[ticker].get_alarm_item(alarm_name)
                alarm.df = alarm.df[alarm.df.index > tool_util.one_week_ago()]
                alarm.tick_df = alarm.tick_df[alarm.tick_df.index > tool_util.one_week_ago()]
            

    def schedule_del_olddf(self):
        # Timer를 생성하고 시작합니다.
        t = threading.Timer(tool_util.delay_h(6), self.schedule_del_olddf)
        t.start()

        self.del_olddf()

    def report_pinned_message(self):
        logging.debug('start report_pinned_message')
 
        message = f'''
        감시중인 Ticker = {[ticker.upper() for ticker in list(self.tickermanager.tickers.keys())]}
        활성화된 User = {list(self.usermanager.users.keys())}
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
            tickers = list(self.tickermanager.tickers.keys())
            for ticker in tickers:

                self.calculate_tick(ticker)

            time.sleep(tool_util.delay_s(10))