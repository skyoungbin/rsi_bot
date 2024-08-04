from mattermostdriver import Driver

import time
import logging
import json 

import websocket
import threading
from requests.exceptions import RequestException

from plotly.io import write_image

import comm_.trade_util as trade_util
import comm_.tool_util as tool_util
import comm_.graph_util as graph_util


class MattermostBot:
    def __init__(self, url, bot_token, team_name, channel_name, event_manager, rsi):

        base_url = url.replace('https://', '').replace('http://', '')
        base_schema = url.split('://')[0]
        self.bot_token = bot_token

        self.initialize_driver(url, bot_token, base_url, base_schema)

        team = self.driver.teams.get_team_by_name(team_name)
        self.team_id = team['id']

        channel = self.driver.channels.get_channel_by_name(self.team_id, channel_name)
        self.channel_id = channel['id']

        self.event_manager = event_manager
        self.rsi = rsi



        # 이벤트 구독
        self.event_manager.subscribe('send_message', self.send_message)
        self.event_manager.subscribe('pinned_message', self.pinned_message)



        # 명령어 핸들러 설정
        self.command_handlers = {
            ###################################
            "!getask": self.handle_command,

            "!add_tickers": self.add_tickers,

            "!del_tickers": self.del_tickers,

            "!update_tickers": self.update_tickers,

            "!all_tickers": self.all_tickers,

            "!active_tickers": self.active_tickers,

            "!status_tickers": self.status_tickers,

            "!get_csv": self.send_csv,

            "!get_graph": self.send_graph,

            #################### alarm ##########################
            "!all_alarms": self.all_alarms,

            "!add_alarms": self.add_alarms,

            "!del_alarms" :self.del_alarms,

            "!update_alarms": self.update_alarms,

            "!get_csv_alarms": self.send_alarm_csv,

            #################### bot ##########################
            "!all_bots": self.all_bots,

            "!add_bots": self.add_bots,

            "!del_bots": self.del_bots,

            "!update_bots": self.update_bots,

            "!get_orderbook_bots": self.send_bot_orderbook,

            "!get_csv_bots": self.send_bot_csv,

            "!get_graph_bots": self.send_bot_graph,

            #################### user ##########################

            "!buy_tickers": self.buy_tickers,

            "!sell_tickers": self.sell_tickers,

            "!get_orderbook": self.send_orderbook,

            "!status_users": self.status_users,
            
            #################### test ##########################
            '!hello': self.message_hello,

            '!help': self.show_help,
        }


        # 웹소켓 연결 설정
        self.websocket_url = f"{url.replace('https', 'wss').replace('http', 'ws')}/api/v4/websocket"
        self.ws = None

        self.send_message('bot online!')

    def initialize_driver(self, url, bot_token, base_url, base_schema):
        initial_delay = 5  # 초 단위
        max_delay = 60  # 최대 1분
        attempt = 0

        while True:
            try:
                self.driver = Driver({
                    'url': base_url,
                    'token': bot_token,
                    'scheme': base_schema,
                    'port': 443,
                    'basepath': '/api/v4',
                    'verify': True,
                })
                self.driver.login()
                logging.info(f"Successfully logged in to Mattermost after {attempt + 1} attempts")
                return
            except RequestException as e:
                attempt += 1
                delay = min(initial_delay * (2 ** (attempt - 1)), max_delay)
                logging.warning(f"Login attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            except Exception as e:
                logging.error(f"Unexpected error during login: {e}")
                raise

    def start_websocket(self):
        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    self.websocket_url,
                    on_message=self.on_websocket_message,
                    on_error=self.on_websocket_error,
                    on_close=self.on_websocket_close,
                    header={"Authorization": f"Bearer {self.bot_token}"}
                )
                self.ws.on_open = self.on_websocket_open
                
                ping_thread = threading.Thread(target=self.ping)
                ping_thread.daemon = True
                ping_thread.start()
                
                self.ws.run_forever()
            except Exception as e:
                logging.error(f"WebSocket connection failed: {e}")
            
            logging.info("Attempting to reconnect in 5 seconds...")
            time.sleep(5)

    def ping(self):
        while self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.sock.ping()
                time.sleep(30)
            except Exception as e:
                logging.error(f"Ping failed: {e}")
                break

    def on_websocket_message(self, ws, message):
        logging.debug(f"Received raw message: {message}")
        try:
            data = json.loads(message)
            if data.get('event') == 'posted':
                post_data = data['data']['post']
                logging.debug(f"Post data (before parsing): {post_data}")
                if isinstance(post_data, str):
                    post = json.loads(post_data)
                else:
                    post = post_data
                logging.debug(f"Parsed post: {post}")
                logging.debug(f"Received command: {post.get('message', 'No message found')}")
                if post['channel_id'] == self.channel_id and post['message'].startswith('!'):
                    self.handle_command(post)
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e}")
            logging.error(f"Problematic JSON: {message}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            logging.error(f"Error details: {str(e)}")

    def on_websocket_open(self, ws):
        logging.info("WebSocket connection opened")

    def on_websocket_error(self, ws, error):
        logging.info(f"WebSocket error: {error}")

    def on_websocket_close(self, ws, close_status_code, close_msg):
        logging.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        if close_status_code is None or close_status_code != 1000:
            # 1000은 정상적인 종료를 의미합니다. 그 외의 경우 재연결을 시도합니다.
            logging.info("Unexpected closure. Reconnecting...")
            self.ws.close()

    def handle_command(self, post):
        try:
            command = post['message'].split()[0]
            logging.debug(f"Handling command: {command}")
            if command in self.command_handlers:
                self.command_handlers[command](post)
            else:
                self.send_message("Unknown command. Type '!help' for a list of available commands.")
        except Exception as e:
            logging.error(f"Error handling command: {e}")
            logging.error(f"Post causing error: {post}")
            self.send_message("An error occurred while processing your command.")

    def send_message(self, message):
        psot = self.driver.posts.create_post({
            'channel_id': self.channel_id,
            'message': message
        })
        return psot

    def start_chat_bot(self):
        websocket_thread = threading.Thread(target=self.start_websocket)
        websocket_thread.start()


    #####################################

    def send_csv(self, post):
        try:
            ticker = tool_util.change_ticker_name(post['message'].split()[1])  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())


            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                self.rsi.tickermanager.tickers[ticker].get_ticker_df().iloc[::-1].to_csv(f'./tmp_/{ticker}.csv')

                with open(f'./tmp_/{ticker}.csv', 'rb') as csv_file:
                    response = self.driver.files.upload_file(
                        channel_id = self.channel_id,
                        files = {'files': (f'{ticker}.csv', csv_file)}
                    )

                file_info = response['file_infos'][0]
                file_id = file_info['id']

                self.driver.posts.create_post({
                    'channel_id': self.channel_id,
                    'message': 'CSV 파일을 업로드합니다.',
                    'file_ids': [file_id]
                })

                response_message = "파일 업로드 완료!"

        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def send_graph(self, post):
        try:
            ticker = tool_util.change_ticker_name(post['message'].split()[1])   # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                fig = graph_util.create_chart(self.rsi.tickermanager.tickers[ticker].get_ticker_df())
                # fig.write_image(f"./tmp_/{ticker}.png")
                write_image(fig, f"./tmp_/{ticker}.png", scale=2.0, width=1920, height=1080)

                with open(f'./tmp_/{ticker}.png', 'rb') as img_file:
                    response = self.driver.files.upload_file(
                        channel_id = self.channel_id,
                        files = {'files': (f'{ticker}.jpg', img_file)}
                    )

                file_info = response['file_infos'][0]
                file_id = file_info['id']

                self.driver.posts.create_post({
                    'channel_id': self.channel_id,
                    'message': 'IMG 파일을 업로드합니다.',
                    'file_ids': [file_id]
                })

                response_message = "파일 업로드 완료!"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)
        
    def add_tickers(self, post):
        ticker = tool_util.change_ticker_name(post['message'].split()[1])  # 사용자가 입력한 텍스트를 가져옵니다
        tickers = list(self.rsi.tickermanager.tickers.keys())
        all_tickers = self.rsi.tickermanager.all_tickers

        if ticker in tickers:
            response_message = f"'{ticker}'는 이미 생성되어있습니다."
        elif ticker in all_tickers:
            #self.rsi.alltickerdata.append_tickers(ticker)
            self.rsi.tickermanager.gen_tickers(ticker)
            response_message = f"'{ticker}'를 추가하였습니다."
        else:
            response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)


    def del_tickers(self, post):

        ticker = tool_util.change_ticker_name(post['message'].split()[1])  # 사용자가 입력한 텍스트를 가져옵니다.
        tickers = list(self.rsi.tickermanager.tickers.keys())
        all_tickers = self.rsi.tickermanager.all_tickers


        if ticker not in tickers and ticker in all_tickers:
            response_message = f"'{ticker}'는 이미 삭제되어있습니다."
        elif ticker in tickers:
            #self.rsi.alltickerdata.remove_tickers(ticker)
            self.rsi.tickermanager.con_tickers(ticker)
            response_message = f"'{ticker}'를 삭제하였습니다."
        else:
            response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)

    def update_tickers(self, post):

        try:

            parts = post['message'].split()
            if len(parts) != 4:
                raise ValueError("Invalid number of arguments")

            _, ticker, params, value = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker에서 선택해주세요."
            else:
                self.rsi.tickermanager.tickers[ticker].update_tickers_params(params, int(value))

                response_message = f"{ticker} params 변경을 완료하였습니다 {params}  {value}"

        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"params 변경 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def all_tickers(self, post):
        self.rsi.tickermanager.update_all_tickers()
        self.send_message(f'사용할 수 있는 Ticker입니다 \n{self.rsi.tickermanager.all_tickers}')

    def active_tickers(self, post):
        self.send_message(f'감시중인 Ticker입니다.\n{list(self.rsi.tickermanager.tickers.keys())}')

    def status_tickers(self, post):
        ticker = tool_util.change_ticker_name(post['message'].split()[1])   # 사용자가 입력한 텍스트를 가져옵니다.
        tickers = list(self.rsi.tickermanager.tickers.keys())
        all_tickers = self.rsi.tickermanager.all_tickers

        if ticker in all_tickers and ticker in tickers:
            self.rsi.update_last_row(ticker, self.rsi.get_upbit_api(ticker))
            ticker_state = self.rsi.tickermanager.tickers[ticker].get_state()
            response_message = f"'{ticker}'의 상태를 불러왔습니다."
            self.send_message(json.dumps(ticker_state, indent=4))
        else:
            response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)


    #################### alarm ##########################
    def all_alarms(self, post):

        self.send_message(f'사용할 수 있는 Alarm입니다 \n{list(self.rsi.alarm_instances.keys())}')

    def add_alarms(self, post):

        parts = post['message'].split()
        if len(parts) != 3:
            raise ValueError("Invalid number of arguments")

        _, ticker, alarm = parts

        ticker = tool_util.change_ticker_name(ticker) 

        tickers = list(self.rsi.tickermanager.tickers.keys())
        alarms = list(self.rsi.tickermanager.tickers[ticker].get_alarm_key())
        all_alarms = list(self.rsi.alarm_instances.keys())

        if ticker in tickers:
            if alarm in alarms:
                response_message = f"'{alarm}'는 이미 생성되어있습니다."
            elif alarm in all_alarms:
                self.rsi.tickermanager.tickers[ticker].add_alarm_key(alarm, self.rsi.alarm_instances[alarm](self.rsi.tickermanager.tickers[ticker]))
                response_message = f"'{alarm}'를 추가하였습니다."
            else:
                response_message = f"'{alarm}'는 알 수 없는 Alarm입니다. 지원하는 Alarm 중에서 선택해주세요."
        else:
            response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)

    def del_alarms(self, post):
        parts = post['message'].split()
        if len(parts) != 3:
            raise ValueError("Invalid number of arguments")

        _, ticker, alarm = parts

        ticker = tool_util.change_ticker_name(ticker) 

        tickers = list(self.rsi.tickermanager.tickers.keys())
        alarms = list(self.rsi.tickermanager.tickers[ticker].get_alarm_key())
        all_alarms = list(self.rsi.alarm_instances.keys())

        if ticker in tickers:
            if alarm not in alarms and alarm in all_alarms:
                response_message = f"'{alarm}'는 이미 삭제되어있습니다."
            elif alarm in alarms:
                self.rsi.tickermanager.tickers[ticker].delete_alarm_key(alarm)
                response_message = f"'{alarm}'를 삭제하였습니다."
            else:
                response_message = f"'{alarm}'는 알 수 없는 Alarm입니다. 지원하는 Alarm 중에서 선택해주세요."
        else:
            response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)

    def update_alarms(self, post):

        try:
            parts = post['message'].split()
            if len(parts) != 5:
                raise ValueError("Invalid number of arguments")

            _, ticker, alarm, params, value = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.

            tickers = list(self.rsi.tickermanager.tickers.keys())
            alarms = list(self.rsi.tickermanager.tickers[ticker].get_alarm_key())
            all_alarms = list(self.rsi.alarm_instances.keys())

            update_values = {}
            update_values[params] = value
            #update_values = dict(zip([params], [value]))

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."
            else:
                if alarm in alarms:

                    self.rsi.tickermanager.tickers[ticker].update_alarm_item(alarm, **update_values)

                    response_message = f"{ticker}-Alarm|{alarm}| params 변경을 완료하였습니다 {params}  {value}"
                else:
                    response_message = f"'{alarm}'는 활성되지 않는 Alarm입니다. 활성한 Alarm 중에서 선택해주세요."

        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"{ticker}-Alarm|{alarm}| params 변경 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def send_alarm_csv(self, post):

        try:
            parts = post['message'].split()
            if len(parts) != 3:
                raise ValueError("Invalid number of arguments")

            _, ticker, alarm = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.

            tickers = list(self.rsi.tickermanager.tickers.keys())
            alarms = list(self.rsi.tickermanager.tickers[ticker].get_alarm_key())

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."
            else:
                if alarm in alarms:

                    alarm = self.rsi.tickermanager.tickers[ticker].get_alarm_item(alarm)

                    alarm.tick_df.iloc[::-1].to_csv(f'./tmp_/{ticker}-{alarm}.csv')

                    with open(f'./tmp_/{ticker}-{alarm}.csv', 'rb') as csv_file:
                        response = self.driver.files.upload_file(
                            channel_id = self.channel_id,
                            files = {'files': (f'{ticker}-{alarm}.csv', csv_file)}
                        )

                    file_info = response['file_infos'][0]
                    file_id = file_info['id']

                    self.driver.posts.create_post({
                        'channel_id': self.channel_id,
                        'message': 'CSV 파일을 업로드합니다.',
                        'file_ids': [file_id]
                    })

                    response_message = "파일 업로드 완료!"
                else:
                    response_message = f"'{alarm}'는 활성되지 않는 Alarm입니다. 활성한 Alarm 중에서 선택해주세요."
        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)


    #################### bot ##########################
    
    def all_bots(self, post):
        self.send_message(f'사용할 수 있는 Bot입니다 \n{list(self.rsi.bot_instances.keys())}')

    def add_bots(self, post):

        parts = post['message'].split()
        if len(parts) != 3:
            raise ValueError("Invalid number of arguments")

        _, ticker, bot = parts

        ticker = tool_util.change_ticker_name(ticker) 

        tickers = list(self.rsi.tickermanager.tickers.keys())
        bots = list(self.rsi.tickermanager.tickers[ticker].get_bot_key())
        all_bots = list(self.rsi.bot_instances.keys())

        if ticker in tickers:
            if bot in bots:
                response_message = f"'{bot}'는 이미 생성되어있습니다."
            elif bot in all_bots:
                self.rsi.tickermanager.tickers[ticker].add_bot_key(bot, self.rsi.bot_instances[bot](self.rsi.tickermanager.tickers[ticker]))
                response_message = f"'{bot}'를 추가하였습니다."
            else:
                response_message = f"'{bot}'는 알 수 없는 Bot입니다. 지원하는 Bot 중에서 선택해주세요."
        else:
            response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)

    def del_bots(self, post):
        parts = post['message'].split()
        if len(parts) != 3:
            raise ValueError("Invalid number of arguments")

        _, ticker, bot = parts

        ticker = tool_util.change_ticker_name(ticker) 

        tickers = list(self.rsi.tickermanager.tickers.keys())
        bots = list(self.rsi.tickermanager.tickers[ticker].get_bot_key())
        all_bots = list(self.rsi.bot_instances.keys())

        if ticker in tickers:
            if bot not in bots and bot in all_bots:
                response_message = f"'{bot}'는 이미 삭제되어있습니다."
            elif bot in bots:
                self.rsi.tickermanager.tickers[ticker].delete_bot_key(bot)
                response_message = f"'{bot}'를 삭제하였습니다."
            else:
                response_message = f"'{bot}'는 알 수 없는 Bot입니다. 지원하는 Bot 중에서 선택해주세요."
        else:
            response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."

        self.send_message(response_message)
        logging.info(response_message)

    def update_bots(self, post):
        try:
            parts = post['message'].split()
            if len(parts) != 5:
                raise ValueError("Invalid number of arguments")

            _, ticker, bot, params, value = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.

            tickers = list(self.rsi.tickermanager.tickers.keys())
            bots = list(self.rsi.tickermanager.tickers[ticker].get_bot_key())
            all_bots = list(self.rsi.bot_instances.keys())

            update_values = {}
            update_values[params] = value

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."
            else:
                if bot in bots:

                    self.rsi.tickermanager.tickers[ticker].update_bot_item(bot, **update_values)

                    response_message = f"{ticker}-Bot|{bot}| params 변경을 완료하였습니다 {params}  {value}"
                else:
                    response_message = f"'{bot}'는 활성되지 않는 Bot입니다. 활성한 Bot 중에서 선택해주세요."

        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"{ticker}-Bot|{bot}| params 변경 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def send_bot_orderbook(self, post):
        try:
            parts = post['message'].split()
            if len(parts) != 3:
                raise ValueError("Invalid number of arguments")

            _,  ticker, bot = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.

            tickers = list(self.rsi.tickermanager.tickers.keys())
            bots = list(self.rsi.tickermanager.tickers[ticker].get_bot_key())

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."
            else:
                if bot in bots:

                    bot = self.rsi.tickermanager.tickers[ticker].get_bot_item(bot)
                    bot.orderbook.iloc[::-1].to_csv(f'./tmp_/{ticker}-{bot}.csv')

                    with open(f'./tmp_/{ticker}-{bot}.csv', 'rb') as csv_file:
                        response = self.driver.files.upload_file(
                            channel_id = self.channel_id,
                            files = {'files': (f'{ticker}-{bot}.csv', csv_file)}
                        )

                    file_info = response['file_infos'][0]
                    file_id = file_info['id']

                    self.driver.posts.create_post({
                        'channel_id': self.channel_id,
                        'message': 'CSV 파일을 업로드합니다.',
                        'file_ids': [file_id]
                    })

                    response_message = "파일 업로드 완료!"
                else:
                    response_message = f"'{bot}'는 활성되지 않는 Bot입니다. 활성한 Bot 중에서 선택해주세요."
        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)


    def send_bot_csv(self, post):

        try:

            parts = post['message'].split()
            if len(parts) != 3:
                raise ValueError("Invalid number of arguments")
            _,  ticker, bot = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.

            tickers = list(self.rsi.tickermanager.tickers.keys())
            bots = list(self.rsi.tickermanager.tickers[ticker].get_bot_key())

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."
            else:
                if bot in bots:

                    bot = self.rsi.tickermanager.tickers[ticker].get_bot_item(bot)

                    bot.df.iloc[::-1].to_csv(f'./tmp_/{ticker}-{bot}.csv')

                    with open(f'./tmp_/{ticker}-{bot}.csv', 'rb') as csv_file:
                        response = self.driver.files.upload_file(
                            channel_id = self.channel_id,
                            files = {'files': (f'{ticker}-{bot}.csv', csv_file)}
                        )

                    file_info = response['file_infos'][0]
                    file_id = file_info['id']

                    self.driver.posts.create_post({
                        'channel_id': self.channel_id,
                        'message': 'CSV 파일을 업로드합니다.',
                        'file_ids': [file_id]
                    })

                    response_message = "파일 업로드 완료!"
                else:
                    response_message = f"'{bot}'는 활성되지 않는 Bot입니다. 활성한 Bot 중에서 선택해주세요."
        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def send_bot_graph(self, post):
        try:
            parts = post['message'].split()
            if len(parts) != 3:
                raise ValueError("Invalid number of arguments")
            _,  ticker, bot = parts

            ticker = tool_util.change_ticker_name(ticker)  # 사용자가 입력한 텍스트를 가져옵니다.

            tickers = list(self.rsi.tickermanager.tickers.keys())
            bots = list(self.rsi.tickermanager.tickers[ticker].get_bot_key())

            if not ticker or ticker not in tickers:
                response_message = f"'{ticker}'는 활성되지 않는 Ticker입니다. 활성한 Ticker 중에서 선택해주세요."
            else:
                if bot in bots:

                    bot = self.rsi.tickermanager.tickers[ticker].get_bot_item(bot)

                    fig = graph_util.create_bot_chart(bot.df)
                    write_image(fig, f"./tmp_/{ticker}-{bot}.png", scale=2.0, width=1920, height=1080)
                    
                    with open(f'./tmp_/{ticker}-{bot}.png', 'rb') as img_file:
                        self.driver.files.upload_file({
                            'channel_id': self.channel_id,
                            'filename': f'{ticker}-{bot}.png',
                            'file': img_file
                        })

                    with open(f'./tmp_/{ticker}-{bot}.png', 'rb') as img_file:
                        response = self.driver.files.upload_file(
                            channel_id = self.channel_id,
                            files = {'files': (f'{ticker}-{bot}.png', img_file)}
                        )

                    file_info = response['file_infos'][0]
                    file_id = file_info['id']

                    self.driver.posts.create_post({
                        'channel_id': self.channel_id,
                        'message': 'IMG 파일을 업로드합니다.',
                        'file_ids': [file_id]
                    })

                    response_message = "파일 업로드 완료!"
                else:
                    response_message = f"'{bot}'는 활성되지 않는 Bot입니다. 활성한 Bot 중에서 선택해주세요."
        except ValueError as ve:
            response_message = f"명령어 형식이 올바르지 않습니다: {str(ve)}"
        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    #################### user ##########################

    def buy_tickers(self, post):
        try:
            ticker = tool_util.change_ticker_name(post['message'].split()[1])   # 사용자가 입력한 텍스트를 가져옵니다.
            tickers = list(self.rsi.tickermanager.tickers.keys())
            all_tickers = self.rsi.tickermanager.all_tickers

            if self.rsi.usermanager.users['default'].purchase_status == True:
                response_message = f"이미 구매한 상태입니다."
            elif ticker in all_tickers and ticker in tickers:
                self.rsi.update_last_row(ticker, self.rsi.get_upbit_api(ticker))
                trade_price = self.rsi.tickermanager.tickers[ticker].get_state()['TickerData']['last_row'][0]['trade_price']

                data = self.rsi.usermanager.users['default'].buy_order(ticker, trade_price)

                response_message = f"'{ticker}'의 구매를 완료하였습니다."
                self.send_message(json.dumps(data))
            else:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        except Exception as e:
            response_message = f"에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def sell_tickers(self, post):
        try:

            if self.rsi.usermanager.users['default'].purchase_status == False:
                response_message = f"이미 판매한 상태입니다."
            elif self.rsi.usermanager.users['default'].purchase_status == True:
                ticker = self.rsi.usermanager.users['default'].buy_ticker
                self.rsi.update_last_row(ticker, self.rsi.get_upbit_api(ticker))
                trade_price = self.rsi.tickermanager.tickers[ticker].get_state()['TickerData']['last_row'][0]['trade_price']

                #getattr(self.rsi, self.buy_ticker).get_state()['tickerData']['last_row'][0]['trade_price']
                data = self.rsi.usermanager.users['default'].sell_order(ticker, trade_price)

                response_message = f"'{ticker}'의 판매를 완료하였습니다."
                self.send_message(json.dumps(data))
            else:
                response_message = f"'{ticker}'는 알 수 없는 Ticker입니다. 지원하는 Ticker 중에서 선택해주세요."

        except Exception as e:
            response_message = f"에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def send_orderbook(self, post):
        try:
            self.rsi.usermanager.users['default'].orderbook.iloc[::-1].to_csv(f'./tmp_/orderbook.csv')

            with open(f'./tmp_/orderbook.csv', 'rb') as csv_file:
                self.driver.files.upload_file({
                    'channel_id': self.channel_id,
                    'filename': 'orderbook.csv',
                    'file': csv_file
                })

            with open(f'./tmp_/orderbook.csv', 'rb') as csv_file:
                response = self.driver.files.upload_file(
                    channel_id = self.channel_id,
                    files = {'files': ('orderbook.csv', csv_file)}
                )

            file_info = response['file_infos'][0]
            file_id = file_info['id']

            self.driver.posts.create_post({
                'channel_id': self.channel_id,
                'message': 'CSV 파일을 업로드합니다.',
                'file_ids': [file_id]
            })

            response_message = "파일 업로드 완료!"

        except Exception as e:
            response_message = f"파일 업로드 에러: {e}"

        self.send_message(response_message)
        logging.info(response_message)

    def status_users(self, post):

        ticker = self.rsi.usermanager.users['default'].buy_ticker
        if ticker is None:
            trade_price = None
        else:
            trade_price = self.rsi.tickermanager.tickers[ticker].get_state()['TickerData']['last_row'][0]['trade_price']
        #getattr(self.rsi, self.buy_ticker).get_state()['tickerData']['last_row'][0]['trade_price'])
        user_state = self.rsi.usermanager.users['default'].get_state(trade_price)
        response_message = f"'user'의 상태를 불러왔습니다."
        self.send_message(json.dumps(user_state, indent=4))

        self.send_message(response_message)
        logging.info(response_message)

    #############################################################

    def pinned_message(self, message):
        # 동작 x
        try:
            # 1. 현재 고정된 모든 메시지를 가져옵니다.
            pinned_posts = self.driver.posts.get_posts_for_channel(self.channel_id, params={'pinned': 'true'})
            

            logging.info(len(pinned_posts['posts'].keys()))

            # 2. 기존의 고정된 메시지들을 모두 해제합니다.
            for post_id in pinned_posts['order']:
                self.driver.posts.update_post({'id': post_id, 'is_pinned': False})
            
            # 3. 새로운 메시지를 채널에 보냅니다.
            new_post = self.send_message(message)

            logging.info(new_post)
            # 4. 새로운 메시지를 고정합니다.
            self.driver.posts.update_post({'id': new_post['id'], 'is_pinned': True})

            response_message = f"새 메시지가 고정되었습니다: {message}"
        except Exception as e:
            response_message = f"메시지 고정 중 오류 발생: {str(e)}"

        self.send_message(response_message)
        logging.info(response_message)



    #####################  test  #########################    
        
    def message_hello(self, post):

        self.send_message(f"Hey there <@{post['user_id']}>!")

    def show_help(self, post):
        try:
            with open('./comm_/commands.json', 'r', encoding='utf-8') as f:
                commands_info = json.load(f)

            help_message = "사용 가능한 명령어 목록:\n\n"
            for command, info in commands_info.items():
                help_message += (
                    f"**명령어**: `{command}`\n"
                    f"**설명**: {info['description']}\n"
                    f"**사용예시**: `{info['example']}`\n\n"
                    "----------------\n"
                )
            response_message = help_message
        except Exception as e:
            response_message = f"Error in show_help: {e}"

        self.send_message(response_message)


