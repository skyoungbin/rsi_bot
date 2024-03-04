from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import time


# Slack 설정
SLACK_BOT_TOKEN = 'xVT'
SLACK_APP_TOKEN = 'xapp77'
CHANNEL_ID = 'C06'

app = App(token=SLACK_BOT_TOKEN)

def send_to_slack():
    try:
        with lock:
            result = client.files_upload(
                channels=CHANNEL_ID,
                file="weather_data.csv"
            )
        time.sleep(1)  # 파일을 업로드한 후에 잠시 기다립니다.
        assert result["file"]  # the uploaded file

    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")

@app.command("/weather")
def handle_weather(ack, say):
    ack()
    send_to_slack()
    say("날씨 데이터가 csv 파일로 저장되어 Slack으로 전송되었습니다.")

@app.message("hello")
def message_hello(message, say):
    say(f"Hey there <@{message['user']}>!")

def send_weather_status(message):
    app.client.chat_postMessage(channel=CHANNEL_ID, text=message)

def start_slack_app():
    SocketModeHandler(app, SLACK_APP_TOKEN).start()