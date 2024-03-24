from slack_bolt import App, Ack, Say, BoltContext
from slack_bolt.adapter.socket_mode import SocketModeHandler

import time
import logging
import json 

from plotly.io import write_image

import comm_.trade_util as trade_util
import comm_.tool_util as tool_util
import comm_.graph_util as graph_util


class SlackBot:
    def __init__(self, SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CHANNEL_ID):
        self.app = App(token=SLACK_BOT_TOKEN)
        self.SLACK_APP_TOKEN = SLACK_APP_TOKEN
        self.CHANNEL_ID = CHANNEL_ID


        self.app.command("/getask")(self.handle_command)

        self.app.command("/get_csv")(self.send_csv_slack)

        self.app.command("/get_rsicsv")(self.send_rsicsv_slack)

        self.app.command("/get_graph")(self.send_graph_slack)

        self.app.command("/add_tickers")(self.add_tickers)

        self.app.command("/del_tickers")(self.del_tickers)

        self.app.command("/update_tickers")(self.update_tickers)

        self.app.command("/all_tickers")(self.all_tickers)

        self.app.command("/active_tickers")(self.active_tickers)

        self.app.command("/status_tickers")(self.status_tickers)

        self.app.command("/buy_tickers")(self.buy_tickers)

        self.app.command("/sell_tickers")(self.sell_tickers)

        self.app.command("/get_orderbook")(self.send_orderbook_slack)

        self.app.command("/status_users")(self.status_users)
        
        self.app.message('hello')(self.message_hello)


    def set_rsi(self, rsi):
        self.rsi = rsi


    def handle_command(self, ack, say):
        ack()
        say("커맨드를 요청하셨습니다...")

    def send_csv_slack(self, ack, say, command):
        ack()
        try:
            ticker = tool_util.change_ticker_name(command['text'])  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())


            if not ticker or ticker.lower() not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                self.rsi.tickermanager.tickers[ticker.lower()].ticker_df.iloc[::-1].to_csv(f'./tmp_/{ticker}.csv')

                response = self.app.client.files_upload_v2(
                    channels=self.CHANNEL_ID,
                    file=f"./tmp_/{ticker}.csv"
                )
                if response["ok"]:
                    response_message = "파일 업로드 완료!"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        say(response_message)
        logging.info(response_message)


    def send_rsicsv_slack(self, ack, say, command):
        ack()
        try:
            ticker = tool_util.change_ticker_name(command['text'])  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())


            if not ticker or ticker.lower() not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                self.rsi.tickermanager.tickers[ticker.lower()].rsi_df.iloc[::-1].to_csv(f'./tmp_/{ticker}_rsi.csv')

                response = self.app.client.files_upload_v2(
                    channels=self.CHANNEL_ID,
                    file=f"./tmp_/{ticker}_rsi.csv"
                )
                if response["ok"]:
                    response_message = "파일 업로드 완료!"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        say(response_message)
        logging.info(response_message)

    def send_graph_slack(self, ack, say, command):
        ack()
        try:
            ticker = tool_util.change_ticker_name(command['text'])  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())

            if not ticker or ticker.lower() not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                fig = graph_util.create_chart(self.rsi.tickermanager.tickers[ticker.lower()].ticker_df, self.rsi.tickermanager.tickers[ticker.lower()].rsi_df)
                # fig.write_image(f"./tmp_/{ticker}.png")
                write_image(fig, f"./tmp_/{ticker}.png", scale=2.0, width=1920, height=1080)

                response = self.app.client.files_upload_v2(
                    channels=self.CHANNEL_ID,
                    file=f"./tmp_/{ticker}.png"
                )
                if response["ok"]:
                    response_message = "파일 업로드 완료!"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        say(response_message)
        logging.info(response_message)
        
    def add_tickers(self, ack, say, command):
        ack()
        ticker = tool_util.change_ticker_name(command['text'])  # 사용자가 입력한 텍스트를 가져옵니다
        tickers = list(self.rsi.tickermanager.tickers.keys())
        all_tickers = self.rsi.tickermanager.all_tickers

        if ticker.lower() in tickers:
            response_message = f"'{ticker}'는 이미 생성되어있습니다."
        elif ticker in all_tickers:
            #self.rsi.alltickerdata.append_tickers(ticker)
            self.rsi.tickermanager.gen_tickers(ticker)
            response_message = f"'{ticker}'를 추가하였습니다."
        else:
            response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        say(response_message)
        logging.info(response_message)


    def del_tickers(self, ack, say, command):
        ack()
        ticker = tool_util.change_ticker_name(command['text'])  # 사용자가 입력한 텍스트를 가져옵니다.
        tickers = list(self.rsi.tickermanager.tickers.keys())
        all_tickers = self.rsi.tickermanager.all_tickers


        if ticker.lower() not in tickers and ticker in all_tickers:
            response_message = f"'{ticker}'는 이미 삭제되어있습니다."
        elif ticker in tickers:
            #self.rsi.alltickerdata.remove_tickers(ticker)
            self.rsi.tickermanager.con_tickers(ticker)
            response_message = f"'{ticker}'를 삭제하였습니다."
        else:
            response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        say(response_message)
        logging.info(response_message)

    def update_tickers(self, ack, say, command):
        ack()

        try:
            ticker, params, value = command["text"].split()
            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())

            if not ticker or ticker.lower() not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                self.rsi.tickermanager.tickers[ticker.lower()].update_tickers_params(params, int(value))

                response_message = f"{ticker} params 변경을 완료하였습니다 {params}  {value}"

        except Exception as e:
            response_message = f"params 변경 에러: {e}"

        say(response_message)
        logging.info(response_message)

    def all_tickers(self, ack, say):
        ack()
        self.rsi.tickermanager.update_all_tickers()
        say(f'사용할 수 있는 Ticker입니다 \n{self.rsi.tickermanager.all_tickers}')

    def active_tickers(self, ack, say):
        ack()
        say(f'감시중인 Ticker입니다.\n{list(self.rsi.tickermanager.tickers.keys())}')

    def status_tickers(self, ack, say, command):
        ack()
        ticker = tool_util.change_ticker_name(command['text']) # 사용자가 입력한 텍스트를 가져옵니다.
        tickers = list(self.rsi.tickermanager.tickers.keys())
        all_tickers = self.rsi.tickermanager.all_tickers

        if ticker in all_tickers and ticker.lower() in tickers:
            self.rsi.update_last_row(ticker, self.rsi.get_upbit_api(ticker))
            ticker_state = self.rsi.tickermanager.tickers[ticker.lower()].get_state()
            response_message = f"'{ticker}'의 상태를 불러왔습니다."
            say(json.dumps(ticker_state, indent=4))
        else:
            response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        say(response_message)
        logging.info(response_message)

    def buy_tickers(self, ack, say, command):
        ack()
        try:
            ticker = tool_util.change_ticker_name(command["text"])  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())
            all_tickers = self.rsi.tickermanager.all_tickers

            if self.rsi.usermanager.users['default'].purchase_status == True:
                response_message = f"이미 구매한 상태입니다."
            elif ticker in all_tickers and ticker.lower() in tickers:
                self.rsi.update_last_row(ticker, self.rsi.get_upbit_api(ticker))
                trade_price = self.rsi.tickermanager.tickers[ticker.lower()].get_state()['TickerData']['last_row'][0]['trade_price']

                data = self.rsi.usermanager.users['default'].buy_order(ticker, trade_price)

                response_message = f"'{ticker}'의 구매를 완료하였습니다."
                say(json.dumps(data))
            else:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        except Exception as e:
            response_message = f"에러: {e}"

        say(response_message)
        logging.info(response_message)

    def sell_tickers(self, ack, say, command):
        ack()
        try:

            if self.rsi.usermanager.users['default'].purchase_status == False:
                response_message = f"이미 판매한 상태입니다."
            elif self.rsi.usermanager.users['default'].purchase_status == True:
                ticker = self.rsi.usermanager.users['default'].buy_ticker
                self.rsi.update_last_row(ticker, self.rsi.get_upbit_api(ticker))
                trade_price = self.rsi.tickermanager.tickers[ticker.lower()].get_state()['TickerData']['last_row'][0]['trade_price']

                #getattr(self.rsi, self.buy_ticker.lower()).get_state()['tickerData']['last_row'][0]['trade_price']
                data = self.rsi.usermanager.users['default'].sell_order(ticker, trade_price)

                response_message = f"'{ticker}'의 판매를 완료하였습니다."
                say(json.dumps(data))
            else:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        except Exception as e:
            response_message = f"에러: {e}"

        say(response_message)
        logging.info(response_message)

    def send_orderbook_slack(self, ack, say, command):
        ack()
        try:
            self.rsi.usermanager.users['default'].orderbook.iloc[::-1].to_csv(f'./tmp_/orderbook.csv')

            response = self.app.client.files_upload_v2(
                channels=self.CHANNEL_ID,
                file=f"./tmp_/orderbook.csv"
            )
            if response["ok"]:
                response_message = "파일 업로드 완료!"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        say(response_message)
        logging.info(response_message)

    def status_users(self, ack, say, command):
        ack()
        ticker = self.rsi.usermanager.users['default'].buy_ticker
        if ticker is None:
            trade_price = None
        else:
            trade_price = self.rsi.tickermanager.tickers[ticker.lower()].get_state()['TickerData']['last_row'][0]['trade_price']
        #getattr(self.rsi, self.buy_ticker.lower()).get_state()['tickerData']['last_row'][0]['trade_price'])
        user_state = self.rsi.usermanager.users['default'].get_state(trade_price)
        response_message = f"'user'의 상태를 불러왔습니다."
        say(json.dumps(user_state, indent=4))

        say(response_message)
        logging.info(response_message)


    def pinned_message(self, message):

        # Step 1: 현재 고정된 모든 메시지의 'ts' 값을 가져옵니다.
        pins_list_response = self.app.client.pins_list(channel=self.CHANNEL_ID)
        pinned_messages_ts = [item["message"]["ts"] for item in pins_list_response["items"]]

        # Step 2: 각 메시지에 대해 'pins.remove' API를 호출하여 고정을 해제합니다.
        for ts in pinned_messages_ts:
            self.app.client.pins_remove(channel=self.CHANNEL_ID, timestamp=ts)
            time.sleep(1)

        # Step 3: 새로운 메시지를 채널에 보내고 'ts' 값을 얻습니다.
        post_message_response = self.app.client.chat_postMessage(
            channel=self.CHANNEL_ID,
            text=message
        )
        new_message_ts = post_message_response["ts"]

        # Step 4: 'pins.add' API를 호출하여 새로운 메시지를 고정합니다.
        self.app.client.pins_add(channel=self.CHANNEL_ID, timestamp=new_message_ts)


    def send_message(self, message):
        self.app.client.chat_postMessage(channel=self.CHANNEL_ID, text=message)
        
    def message_hello(self, message, say):
        say(f"Hey there <@{message['user']}>!")

    def start_slack_app(self):
        SocketModeHandler(self.app, self.SLACK_APP_TOKEN).start()

