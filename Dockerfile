FROM python:3.8-buster

WORKDIR /home/sc-twitter-bot

RUN apt-get update &&\
    DEBIAN_FRONTEND='noninteractive' apt-get install -y ffmpeg supercollider

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

CMD ["python", "start_bot.py"]
