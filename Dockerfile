FROM python:3.10-bullseye

WORKDIR /home/sc-twitter-bot

RUN apt-get update && apt-get install -y \
    ffmpeg \
    acl \
    && rm -rf /var/lib/apt/lists/*

# install headless SC via building script
ADD install_sc.sh .
RUN ./install_sc.sh

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

# do not allow sc to access our directory
RUN adduser --disabled-password --gecos "" sc && \
    chmod u+s /usr/local/bin/sclang && \
    chmod u+s /usr/local/bin/scsynth

ENV PYTHONUNBUFFERED=0

CMD ["/bin/sh", "-c", \
    "setfacl -m u:sc:--- /home/sc-twitter-bot && python /home/sc-twitter-bot/start_bot.py" \
]
