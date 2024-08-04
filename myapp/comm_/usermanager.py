import os
import shutil

import dill as pickle
import threading
import logging

from comm_.userdata import UserData



class UserManager:
    
    def __init__(self):

        self.file_path = './data_/users.pkl'
        self.backup_path = './data_/users_backup.pkl'


        self._users = {}

        self.users_lock = threading.Lock()
        self.save_lock = threading.Lock()

    # def save_users(self):
    #     with open('./data_/users.pkl', 'wb') as f:
    #         pickle.dump(self, f)
    
    # @classmethod
    # def load_users(cls):
    #     with open('./data_/users.pkl', 'rb') as f:
    #         manager = pickle.load(f)
    #     return manager

    # def __getstate__(self):
    #     state = self.__dict__.copy()

    #     del state['users_lock']

    #     return state

    # def __setstate__(self, state):
    #     self.__dict__.update(state)

    #     self.users_lock = threading.Lock()

    def to_dict(self):
        return {
            'users': {username: user.to_dict() for username, user in self.users.items()}
        }

    @classmethod
    def from_dict(cls, data):
        manager = cls()
        manager._users = {username: UserData.from_dict(user_data) for username, user_data in data['users'].items()}

        return manager

    def save_users(self):
        save_thread = threading.Thread(target=self._save_users_thread)
        save_thread.start()
        return save_thread

    def _save_users_thread(self):
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
                logging.error(f"Failed to save users: {e}")
                # 저장 실패 시 백업에서 복원
                if os.path.exists(self.backup_path):
                    shutil.copy2(self.backup_path, self.file_path)
                    logging.info("Restored from backup")
                else:
                    logging.warning("No backup file found to restore from")
    
    @classmethod
    def load_users(cls):
        try:
            with open('./data_/users.pkl', 'rb') as f:
                data = pickle.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logging.error(f"Failed to save tickers: {e}")


    @property
    def users(self):
        with self.users_lock:
            return self._users

    def gen_users(self, users):
        if isinstance(users, str):
            users = [users]
        for trader in users:
            if trader.upper() not in self.users:
                user = UserData()
                user.manager = self
                self.users[trader.upper()] = user
        self.save_users()

    def con_users(self, users):
        trader = users.upper()
        if trader in self.users:
            del self.users[trader]
        self.save_users()
