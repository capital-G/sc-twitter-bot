import logging
import re
import subprocess
import tempfile
import time
from typing import Optional
import threading
import re
import random

from PIL import Image, ImageDraw, ImageFont, ImageColor
import tweepy

from . import SuperColliderConverter, ConverterException

log = logging.getLogger(__name__)


class TwitterBot:
    def __init__(
        self,
        bearer_token: str,
        consumer_key: str,
        consumer_secret: str,
        access_token_key: str,
        access_token_secret: str,
        connect: bool = True,
        **kwargs,
    ):
        self.sc_converter = SuperColliderConverter(**kwargs)
        self.bearer_token = bearer_token
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token_key = access_token_key
        self.access_token_secret = access_token_secret

        # for testing purposes we make connecting optional
        if connect:
            # inits streaming_client, client and screen name
            self._twitter_login()
        else:
            self.bot_screen_name = "sc2sbot"
            self.own_user_id = 0

    def _twitter_login(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token_key, self.access_token_secret)

        # traditional client for posting
        # we use v1 as uploading media is not supported yet
        self.client = tweepy.API(auth)
        try:
            user: tweepy.User = self.client.verify_credentials()
            self.bot_screen_name = user.screen_name
            self.own_user_id = user.id
            log.info(
                f"Successfully authenticated at Twitter posting API as {self.bot_screen_name}"
            )
        except tweepy.TweepyException as e:
            log.error(f"Could not authenticate! {e}")
            raise e

        # streaming client for receiving
        self.streaming_client = tweepy.StreamingClient(bearer_token=self.bearer_token)
        self.streaming_client.on_tweet = self.on_tweet

        # reset rules
        active_rules = self.streaming_client.get_rules()
        if active_rules.data:
            self.streaming_client.delete_rules([r.id for r in active_rules.data])
        self.streaming_client.add_rules(tweepy.StreamRule(f"@{self.bot_screen_name}"))

    def start(self) -> None:
        try:
            log.info("Start looking for tweets via streaming API")
            self.streaming_client.filter(
                tweet_fields=[
                    "entities",
                    "author_id",
                ]
            )
        except KeyboardInterrupt:
            pass
        finally:
            log.info("Disconnect from streaming API")
            self.streaming_client.disconnect()
        log.info("Stopped looking for tweets")

    def on_tweet(self, tweet: tweepy.Tweet):
        if tweet.author_id != self.own_user_id:
            threading.Thread(target=self.process_tweet(tweet))
        else:
            log.debug(f"Ignored own tweet {tweet}")

    def process_tweet(self, tweet: tweepy.Tweet):
        log.info(f"Received tweet from @{tweet.author_id}: {tweet.text}")
        try:
            self.post_supercollider_sound_tweet(
                self._filter_out_synth_def(tweet),
                reply_tweet=tweet,
            )
        except ConverterException:
            log.error(f"Could not render audio from {tweet}")
            return

    def _create_image_from_code(
        self,
        code: str,
        image_path: str,
        source_image_path: str = "sc.png",
        font_file="RobotoMono-Medium.ttf",
    ) -> None:
        image = Image.open(source_image_path)
        image_draw = ImageDraw.Draw(image)
        for _ in range(40):
            image_draw.text(
                # random position
                (
                    random.randint((-1) * image.size[0] / 2, image.size[0] * 0.75),
                    random.randint(0, image.size[1]),
                ),
                code,
                # color should be a lighter shade
                [int(255 * (random.random() * 0.25 + 0.75)) for _ in range(3)],
                font=ImageFont.truetype(font=font_file, size=random.randint(10, 40)),
            )
        # create a line break every 32 chars
        code = "".join(code[i : i + 32] + "\n" for i in range(0, len(code), 32))

        # find a good size for the main font
        font = ImageFont.truetype(font=font_file, size=max(60, int(1800 / (len(code)))))
        # get text position so we can center it
        w, h = image_draw.textsize(code, font=font)

        image_draw.text(
            ((image.size[0] - w) / 2, (image.size[1] - h) / 2),
            code,
            font=font,
            fill=ImageColor.getrgb(
                f"hsv({random.randint(0, 100)},{random.randint(80, 100)}%,{random.randint(50, 100)}%)"
            ),
        )

        image.save(image_path)

    def _convert_to_video(
        self,
        sc_code: str,
        video_path: str,
        source_image_path: str = "sc.png",
        debug: bool = True,
    ):
        with tempfile.NamedTemporaryFile(suffix=".wav") as wav_file:
            self.sc_converter.record_sc_code(sc_code, wav_file.name)
            with tempfile.NamedTemporaryFile(suffix=".png") as png_file:
                self._create_image_from_code(
                    sc_code, png_file.name, source_image_path=source_image_path
                )
                # from https://gist.github.com/nikhan/26ddd9c4e99bbf209dd7
                subprocess.run(
                    [
                        "ffmpeg",
                        "-loop",
                        "1",
                        "-y",
                        "-i",
                        png_file.name,
                        "-i",
                        wav_file.name,
                        "-shortest",
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        "-r",
                        "30",
                        "-acodec",
                        "aac",
                        "-b:a",
                        "128k",
                        "-ar",
                        "48000",
                        "-ac",
                        "2",
                        video_path,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT if debug else subprocess.PIPE,
                )
                log.debug(f"Converted {wav_file.name} to {video_path}")

    @staticmethod
    def _convert_urls_to_sc_code(tweet: tweepy.Tweet) -> str:
        """
        SC code gets interpreted as URLs why we need to convert them back to their original state by
        replacing the URLs with the displayed URL.

        :param tweet:
        :return: tweet text w/ urls (SinOsc.ar gets t.co/fda) -> actual tweet text
        """
        tweet_text = str(tweet.text)
        for url_entity in tweet.entities.get("urls", []):
            tweet_text = tweet_text.replace(
                url_entity["url"], url_entity["display_url"]
            )
        return tweet_text

    def _get_username(self, tweet: tweepy.Tweet) -> str:
        if tweet.author_id:
            user: tweepy.User = self.client.get_user(user_id=tweet.author_id)
            return str(user.screen_name)
        else:
            log.error(f"Missing author ID: {tweet}")
            return ""

    def post_supercollider_sound_tweet(
        self, sc_synth_def: str, reply_tweet: Optional[tweepy.Tweet] = None
    ):
        if reply_tweet:
            username = "@{}".format(self._get_username(reply_tweet))
        else:
            username = ""

        video_file = tempfile.NamedTemporaryFile(suffix=".mp4")
        self._convert_to_video(sc_synth_def, video_file.name)
        media = self.client.media_upload(
            video_file.name,
            media_category="tweet_video",
        )

        time.sleep(5)  # hack b/c twitter api takes time after upload of media

        status = self.client.update_status(
            "{username} {synth_text}".format(
                username=username,
                synth_text=(sc_synth_def[:100] + "...")
                if len(sc_synth_def) > 100
                else sc_synth_def,
            ).strip(),
            in_reply_to_status_id=reply_tweet.id if reply_tweet else None,
            media_ids=[media.media_id],
        )
        log.info(f"Posted response {status.id}: {status.text}")
        video_file.close()

    def _filter_out_synth_def(self, tweet: tweepy.Tweet) -> str:
        text = self._convert_urls_to_sc_code(tweet)
        twitter_name_filter = re.compile(
            re.escape(f"@{self.bot_screen_name}"), re.IGNORECASE
        )
        text = twitter_name_filter.sub("", text).strip()
        # remove hashtags
        text = re.sub(r"#\S*", "", text).strip()
        log.debug(f"Filtered out {text} from {tweet.text}")
        return text
