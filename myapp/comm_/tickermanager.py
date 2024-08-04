import os
import shutil

import dill as pickle
import threading
import pyupbit
import logging

#import comm_.tickerdata as tickerdata
from comm_.tickerdata import TickerData
import comm_.tool_util as tool_util



class TickerManager:

    def __init__(self):
        
        self.file_path = './data_/tickers.pkl'
        self.backup_path = './data_/tickers_backup.pkl'

        self._all_tickers = []
        self._tickers = {}

        self.all_tickers_lock = threading.Lock()
        self.tickers_lock = threading.Lock()
        self.save_lock = threading.Lock()

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

    # def save_tickers(self):
    #     with open('./data_/tickers.pkl', 'wb') as f:
    #         pickle.dump(self, f)

    # @classmethod
    # def load_tickers(cls):
    #     with open('./data_/tickers.pkl', 'rb') as f:
    #         manager = pickle.load(f)
    #     return manager

    # def __getstate__(self):
    #     state = self.__dict__.copy()

    #     del state['all_tickers_lock']
    #     del state['tickers_lock']

    #     return state

    # def __setstate__(self, state):

    #     self.__dict__.update(state)

    #     self.all_tickers_lock = threading.Lock()
    #     self.tickers_lock = threading.Lock()
    
    def to_dict(self):
        return {
            'all_tickers': self._all_tickers,
            'tickers': {symbol: ticker.to_dict() for symbol, ticker in self.tickers.items()}
        }

    @classmethod
    def from_dict(cls, data, alarm_instances, bot_instances):
        manager = cls()
        manager._all_tickers = data['all_tickers']
        manager._tickers = {
            symbol: TickerData.from_dict(ticker_data, alarm_instances, bot_instances) 
            for symbol, ticker_data in data['tickers'].items()
        }
        for ticker in manager._tickers.values():
            ticker.manager = manager
        return manager

    def save_tickers(self):
        save_thread = threading.Thread(target=self._save_tickers_thread)
        save_thread.start()
        return save_thread

    # def _save_tickers_thread(self):
    #     try:
    #         with open('./data_/tickers.pkl', 'wb') as f:
    #             pickle.dump(self.to_dict(), f)
    #     except Exception as e:
    #         logging.error(f"Failed to save tickers: {e}")

    def _save_tickers_thread(self):
        with self.save_lock:
            try:
                # 1. 현재 파일을 백업 (존재하는 경우)
                if os.path.exists(self.file_path):
                    shutil.copy2(self.file_path, self.backup_path)
                    logging.debug("Backup created")

                # 2. 새 데이터 저장
                with open(self.file_path, 'wb') as f:
                    pickle.dump(self.to_dict(), f)
                logging.debug("New data saved successfully")

                # 3. 백업 파일 삭제
                if os.path.exists(self.backup_path):
                    os.remove(self.backup_path)
                    logging.debug("Backup removed")

            except Exception as e:
                logging.error(f"Failed to save tickers: {e}")
                # 저장 실패 시 백업에서 복원
                if os.path.exists(self.backup_path):
                    shutil.copy2(self.backup_path, self.file_path)
                    logging.info("Restored from backup")
                else:
                    logging.warning("No backup file found to restore from")

    @classmethod
    def load_tickers(cls, alarm_instances, bot_instances):
        try:
            with open('./data_/tickers.pkl', 'rb') as f:
                data = pickle.load(f)
            return cls.from_dict(data, alarm_instances, bot_instances)
        except Exception as e:
            logging.error(f"Failed to save tickers: {e}")


    @property
    def tickers(self):
        with self.tickers_lock:
            return self._tickers

    def gen_tickers(self, ticker_symbols):
        if isinstance(ticker_symbols, str):
            ticker_symbols = [ticker_symbols]
        for symbol in ticker_symbols:
            if symbol.upper() not in self.tickers:
                ticker = TickerData(symbol.upper())
                ticker.manager = self
                self.tickers[symbol.upper()] = ticker
        self.save_tickers()
    
    def con_tickers(self, ticker_symbol):
        symbol = ticker_symbol.upper()
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