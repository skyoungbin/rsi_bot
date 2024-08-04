
import os
import logging
import threading 

import main_upbit as main_upbit
import main_mattermost as main_chat
from comm_.event_manager import EventManager

def set_folders():
    try:
        if not os.path.exists("log_"):
            os.mkdir("log_")
    except OSError:
        print ('Error: Creating directory. ' +  "log_")
        
    try:
        if not os.path.exists("tmp_"):
            os.mkdir("tmp_")
    except OSError:
        print ('Error: Creating directory. ' +  "tmp_")

    try:
        if not os.path.exists("data_"):
            os.mkdir("data_")
    except OSError:
        print ('Error: Creating directory. ' +  "data_")

def set_logging(log_level):

    # 로그 생성
    logger = logging.getLogger()
    # 로그 레벨 문자열을 적절한 로깅 상수로 변환
    log_level_constant = getattr(logging, log_level, logging.INFO)
    # 로그의 출력 기준 설정
    logger.setLevel(log_level_constant)
    # log 출력 형식
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # log를 console에 출력
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    # log를 파일에 출력
    #file_handler = logging.FileHandler('GoogleTrendsBot.log')
    #file_handler.setFormatter(formatter)
    #logger.addHandler(file_handler)



if __name__ == "__main__":


    #SLACK_BOT_TOKEN=os.getenv('SLACK_BOT_TOKEN')
    #SLACK_APP_TOKEN=os.getenv('SLACK_APP_TOKEN')
    #CHANNEL_ID=os.getenv('CHANNEL_ID')

    MATTERMOST_URL =os.getenv('MATTERMOST_URL')
    MATTERMOST_ACCESS_TOKEN =os.getenv('MATTERMOST_ACCESS_TOKEN')
    MATTERMOST_CHANNEL_NAME =os.getenv('MATTERMOST_CHANNEL_NAME')
    MATTERMOST_TEAM_NAME =os.getenv('MATTERMOST_TEAM_NAME')

    set_folders()
    set_logging('INFO')
    event_manager = EventManager()

    upbit = main_upbit.Notifier(event_manager)
    chat = main_chat.MattermostBot(MATTERMOST_URL, MATTERMOST_ACCESS_TOKEN, MATTERMOST_TEAM_NAME, MATTERMOST_CHANNEL_NAME, event_manager, upbit)
    
    

    upbit.set_schedule()

    upbit_thread = threading.Thread(target=upbit.run)
    chat_thread = threading.Thread(target=chat.start_chat_bot)


    upbit_thread.start()
    chat_thread.start()

    slack_thread.join()
