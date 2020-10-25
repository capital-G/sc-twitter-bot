FROM python:3.8-buster

WORKDIR /home/sc-twitter-bot

RUN apt-get update && apt-get install -y ffmpeg

# install headless SC via building script
ADD install_sc.sh .
RUN ./install_sc.sh

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

CMD ["python", "/home/sc-twitter-bot/start_bot.py"]
