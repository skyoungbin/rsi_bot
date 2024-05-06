
import os
import logging
import threading 

import main_upbit as main_upbit
import main_slack as main_slack

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


    SLACK_BOT_TOKEN=os.getenv('SLACK_BOT_TOKEN')
    SLACK_APP_TOKEN=os.getenv('SLACK_APP_TOKEN')
    CHANNEL_ID=os.getenv('CHANNEL_ID')

    set_folders()
    set_logging('INFO')


    upbit = main_upbit.Notifier()
    slack = main_slack.SlackBot(SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CHANNEL_ID)
    
    slack.set_rsi(upbit)
    upbit.set_slack(slack.send_message, slack.pinned_message)

    upbit.set_schedule()

    upbit_thread = threading.Thread(target=upbit.run)
    slack_thread = threading.Thread(target=slack.start_slack_app)


    upbit_thread.start()
    slack_thread.start()

    slack_thread.join()
