import logging
import re
import subprocess
import tempfile
import time
from typing import Optional

import tweepy

from sc_twitter_bot.sc_converter import SuperColliderConverter, ConverterException

log = logging.getLogger(__name__)


class TwitterBot:
    def __init__(
            self,
            consumer_key: str,
            consumer_secret: str,
            access_token_key: str,
            access_token_secret: str,
            do_login: bool = True,
            sleep_time: int = 5 * 60,
            bot_screen_name: str = 'sc2sbot',
            **kwargs,
    ):
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token_key, access_token_secret)
        self.sc_converter = SuperColliderConverter(**kwargs)
        self.sleep_time = sleep_time
        self.bot_screen_name = bot_screen_name

        self.api = tweepy.API(self.auth)
        if do_login:
            self._login()

    def _login(self):
        try:
            self.api.verify_credentials()
            log.info('Successfully authenticated at Twitter')
        except Exception as e:
            log.error(f'Could not authenticate! {e}')
            raise e

    def _convert_to_video(self, sc_synthdef: str, video_path: str, picture_file_path: str = 'sc.png',
                          debug: bool = True):
        with tempfile.NamedTemporaryFile(suffix='.wav') as wav_file:
            self.sc_converter.playback_synthdef(sc_synthdef, wav_file.name)
            # from https://gist.github.com/nikhan/26ddd9c4e99bbf209dd7
            subprocess.run([
                'ffmpeg',
                '-loop', '1',
                '-y',
                '-i', picture_file_path,
                '-i', wav_file.name,
                '-shortest',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                '-acodec', 'aac',
                '-ar', '44100',
                '-ac', '2',
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT if debug else subprocess.PIPE)

            log.debug(f'Converted {wav_file.name} to {video_path}')

    @staticmethod
    def _convert_urls_to_sc_code(tweet: tweepy.models.Status) -> str:
        """
        SC code gets interpreted as URLs why we need to convert them back to their original state by
        replacing the URLs with the displayed URL.

        :param tweet:
        :return: tweet text w/ urls (SinOsc.ar gets t.co/fda) -> actual tweet text
        """
        tweet_text = str(tweet.full_text)
        for url_entity in tweet.entities['urls']:
            tweet_text = tweet_text.replace(url_entity['url'], url_entity['display_url'])
        return tweet_text

    def post_supercollider_sound_tweet(self, sc_synth_def: str, reply_tweet: Optional[tweepy.models.Status] = None):
        video_file = tempfile.NamedTemporaryFile(suffix='.mp4')
        self._convert_to_video(sc_synth_def, video_file.name)
        media = self.api.media_upload(video_file.name)
        time.sleep(5)  # hack b/c twitter api takes time after upload of media
        self.api.update_status(
            '@{username} {synth_text}'.format(
                username=reply_tweet.user.screen_name if reply_tweet else ' ',
                synth_text=(sc_synth_def[:100] + '...') if len(sc_synth_def) > 100 else sc_synth_def
            ),
            reply_tweet_id=reply_tweet.id if reply_tweet else None,
            media_ids=[media.media_id],
        )
        video_file.close()

    def _filter_out_synth_def(self, tweet: tweepy.models.Status) -> str:
        text = self._convert_urls_to_sc_code(tweet)
        twitter_name_filter = re.compile(re.escape(f'@{self.bot_screen_name}'), re.IGNORECASE)
        text = twitter_name_filter.sub('', text).strip()
        log.debug(f'Filtered out {text} from {tweet.full_text}')
        return text

    def look_for_mentions(self):
        start_mentions = self.api.mentions_timeline(tweet_mode='extended')
        seen_mention_ids = set([s.id for s in start_mentions])
        while True:
            new_mentions = self.api.mentions_timeline(tweet_mode='extended')
            mention: tweepy.models.Status
            for mention in [m for m in new_mentions if m.id not in seen_mention_ids]:
                log.info(f"New mention from @{mention.user.screen_name}: {mention.full_text}")
                try:
                    self.post_supercollider_sound_tweet(
                        sc_synth_def=self._filter_out_synth_def(mention),
                        reply_tweet=mention,
                    )
                    log.info(f'Successfully posted tweet response to {mention.full_text}')
                except ConverterException as e:
                    log.info(f'Could not convert SynthDef {mention.full_text} to audio: {e}')
            seen_mention_ids = set([s.id for s in new_mentions])
            log.debug(f'Go sleeping for {self.sleep_time} seconds')
            time.sleep(self.sleep_time)
