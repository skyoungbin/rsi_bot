import pickle
import threading
from comm_.userdata import UserData



class UserManager:
    
    def __init__(self):
        self._users = {}

        self.users_lock = threading.Lock()

    def save_users(self):
        with open('./data_/users.pkl', 'wb') as f:
            pickle.dump(self, f)
    
    @classmethod
    def load_users(cls):
        with open('./data_/users.pkl', 'rb') as f:
            manager = pickle.load(f)
        return manager

    def __getstate__(self):
        state = self.__dict__.copy()

        del state['users_lock']

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self.users_lock = threading.Lock()

    @property
    def users(self):
        with self.users_lock:
            return self._users

    def gen_users(self, users):
        if isinstance(users, str):
            users = [users]
        for trader in users:
            if trader.lower() not in self.users:
                user = UserData()
                user.manager = self
                self.users[trader.lower()] = user
        self.save_users()

    def con_users(self, users):
        trader = users.lower()
        if trader in self.users:
            del self.users[trader]
        self.save_users()
