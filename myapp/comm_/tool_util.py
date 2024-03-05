from datetime import datetime, timedelta, time
from pytz import timezone


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