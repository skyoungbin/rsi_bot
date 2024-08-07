FROM python:3.10.13-slim

WORKDIR /usr/src/app

COPY . .

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

WORKDIR ./myapp

#ENV TOCKEN=tocken
#ENV CHAT_ID=chat_id
#ENV SLACK_BOT_TOKEN=SLACK_BOT_TOKEN
#ENV SLACK_APP_TOKEN=SLACK_APP_TOKEN
#ENV CHANNEL_ID=CHANNEL_ID
ENV MATTERMOST_URL =default
ENV MATTERMOST_ACCESS_TOKEN =default
ENV MATTERMOST_CHANNEL_NAME =default
ENV MATTERMOST_TEAM_NAME =default
CMD [ "python","main.py" ]