import logging
import os

from sc_twitter_bot import TwitterBot

logger = logging.getLogger("sc_twitter_bot")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

if __name__ == "__main__":
    twitter_bot = TwitterBot(
        bearer_token=os.environ["API_BEARER_TOKEN"],
        consumer_key=os.environ["API_KEY"],
        consumer_secret=os.environ["API_KEY_SECRET"],
        access_token_key=os.environ["API_ACCESS_TOKEN"],
        access_token_secret=os.environ["API_ACCESS_TOKEN_SECRET"],
    )
    twitter_bot.start()
