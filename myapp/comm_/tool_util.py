from datetime import datetime, timedelta, time
from pytz import timezone
import pickle
import os
import importlib.util

def get_kr_time():
    return datetime.now(timezone('Asia/Seoul'))

def one_week_ago():
    now = get_kr_time()
    return datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(weeks=1)

def delay_h(hour):
    now = get_kr_time()
    next_noon = datetime.combine(now.date() + timedelta(days=1), time(hour),tzinfo=now.tzinfo)
    return (next_noon - now).total_seconds()

def delay_s(sec):
    now = get_kr_time()
    return sec - now.second % sec

def delay_1m():
    now = get_kr_time()
    return 60 - now.second

def delay_every_6h():
    # 현재 시간을 가져옵니다.
    now = get_kr_time()

    # 가장 가까운 다음 0시, 6시, 12시, 18시를 계산합니다.
    next_hour = ((now.hour // 6) + 1) * 6 % 24
    if next_hour <= now.hour:
        next_day = now + datetime.timedelta(days=1)
        next_time = datetime.datetime(next_day.year, next_day.month, next_day.day, next_hour)
    else:
        next_time = datetime.datetime(now.year, now.month, now.day, next_hour)

    return (next_time - now).total_seconds()


def change_ticker_name(ticker):
    return f'KRW-{ticker.upper()}'


def load_alarm_instances(folder_path):
    """알람 모듈의 클래스를 딕셔너리 형태로 로드하는 함수."""
    alarm_instances = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.py'):
            module_name = filename[:-3]  # 파일 확장자 제거
            module_path = os.path.join(folder_path, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # 모듈 내의 첫 번째 클래스를 찾음
            AlarmClass = getattr(module, 'Alarm', None)
            if AlarmClass:
                # 클래스 자체를 딕셔너리에 저장, 키는 모듈 이름(파일 이름)
                alarm_instances[module_name] = AlarmClass
    return alarm_instances


def load_bot_instances(folder_path):
    """알람 모듈의 클래스를 딕셔너리 형태로 로드하는 함수."""
    bot_instances = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.py'):
            module_name = filename[:-3]  # 파일 확장자 제거
            module_path = os.path.join(folder_path, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # 모듈 내의 첫 번째 클래스를 찾음
            BotClass = getattr(module, 'Bot', None)
            if BotClass:
                # 클래스 자체를 딕셔너리에 저장, 키는 모듈 이름(파일 이름)
                bot_instances[module_name] = BotClass
    return bot_instances