from slack_bolt import App, Ack, Say, BoltContext
from slack_bolt.adapter.socket_mode import SocketModeHandler

#from slack_bolt.async_app import AsyncApp, AsyncRespond, AsyncAck, AsyncSay
#from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import time
import logging
import json 

class SlackBot:
    def __init__(self, SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CHANNEL_ID):
        self.app = App(token=SLACK_BOT_TOKEN)
        self.SLACK_APP_TOKEN = SLACK_APP_TOKEN
        self.CHANNEL_ID = CHANNEL_ID


        self.app.command("/getask")(self.handle_command)

        self.app.command("/get_csv")(self.send_csv_slack)

        self.app.command("/add_tickers")(self.add_tickers)

        self.app.command("/del_tickers")(self.del_tickers)

        self.app.command("/all_tickers")(self.all_tickers)

        self.app.command("/active_tickers")(self.active_tickers)

        self.app.command("/status_tickers")(self.status_tickers)
        
        self.app.message('hello')(self.message_hello)


    def set_rsi(self, rsi):
        self.rsi = rsi

    def handle_command(self, ack, say):
        ack()
        say("커맨드를 요청하셨습니다...")

    def send_csv_slack(self, ack, say, command):
        ack()
        try:
            ticker = command['text']  # 사용자가 입력한 텍스트를 가져옵니다.
            ticker = f'KRW-{ticker.upper()}'
            if not ticker or ticker not in self.rsi.tickers:
                say(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요.")
                logging.info(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요.")
                return
            with getattr(self.rsi, ticker.lower()).lock:
                getattr(self.rsi, ticker.lower()).ticker_df.iloc[::-1].to_csv(f'./tmp_/{ticker}.csv')
                response = self.app.client.files_upload_v2(
                    channels=self.CHANNEL_ID,
                    file=f"./tmp_/{ticker}.csv"
                )
            if response["ok"]:
                logging.info("파일 업로드 완료!")
        except Exception as e:
            logging.info(f"파일 업로드 에러: {e}")
        
        time.sleep(1)  # 파일을 업로드한 후에 잠시 기다립니다.

    def add_tickers(self, ack, say, command):
        ack()
        ticker = command['text']  # 사용자가 입력한 텍스트를 가져옵니다.
        ticker = f'KRW-{ticker.upper()}' 
        
        if ticker not in self.rsi.tickers:
            if ticker in self.rsi.all_tickers:  
                self.rsi.tickers.append(ticker)
                self.rsi.gen_tickers(ticker)
                say(f"'{ticker}'를 추가하였습니다.")
                logging.info(f"'{ticker}'를 추가하였습니다.")
            else:
                say(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요.")
                logging.info(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요.")
        else:
            say(f"'{ticker}'는 이미 생성되어있습니다.")
            logging.info(f"'{ticker}'는 이미 생성되어있습니다.")


    def del_tickers(self, ack, say, command):
        ack()
        ticker = command['text']  # 사용자가 입력한 텍스트를 가져옵니다.
        ticker = f'KRW-{ticker.upper()}' 

        if ticker in self.rsi.all_tickers and ticker in self.rsi.tickers:
            self.rsi.tickers.remove(ticker)
            self.rsi.con_tickers(ticker)
            say(f"'{ticker}'를 삭제하였습니다.")
            logging.info(f"'{ticker}'를 삭제하였습니다.")
        else:
            say(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요.")
            logging.info(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요.")

    def all_tickers(self, ack, say):
        ack()
        self.rsi.update_all_tickers()
        say(f'사용할 수 있는 Ticker입니다 \n{self.rsi.all_tickers}')

    def active_tickers(self, ack, say):
        ack()
        say(f'감시중인 Ticker입니다.\n{self.rsi.tickers}')

    def status_tickers(self, ack, say, command):
        ack()
        ticker = command['text']  # 사용자가 입력한 텍스트를 가져옵니다.
        ticker = f'KRW-{ticker.upper()}' 

        if ticker in self.rsi.all_tickers and ticker in self.rsi.tickers:
            with getattr(self.rsi, ticker.lower()).lock:
                ticker_state = getattr(self.rsi, ticker.lower()).get_state()
                logging.info(ticker_state)
                say(json.dumps(ticker_state, indent=4))
                say(f"'{ticker}'를 상태를 불러왔습니다.")
                logging.info(f"'{ticker}'를 상태를 불러왔습니다.")
        else:
            say(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요.")
            logging.info(f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요.")



    def send_message(self, message):
        self.app.client.chat_postMessage(channel=self.CHANNEL_ID, text=message)
        
    def message_hello(self, message, say):
        say(f"Hey there <@{message['user']}>!")

    def start_slack_app(self):
        SocketModeHandler(self.app, self.SLACK_APP_TOKEN).start()

