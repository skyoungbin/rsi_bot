FROM python:3.10.13-slim

WORKDIR /usr/src/app

COPY . .

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

WORKDIR ./myapp

ENV TOCKEN=tocken
ENV CHAT_ID=chat_id

CMD [ "python","main.py" ]