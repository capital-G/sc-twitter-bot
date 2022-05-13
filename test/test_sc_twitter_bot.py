from unittest import TestCase
from unittest.mock import MagicMock

from sc_twitter_bot.sc_twitter_bot import TwitterBot


class TwitterBotTestCase(TestCase):
    def setUp(self) -> None:
        self.twitter_bot = TwitterBot(
            bearer_token="",
            consumer_key="",
            consumer_secret="",
            access_token_key="",
            access_token_secret="",
            connect=False,
        )

    def test_convert_urls_to_sc_code(self):
        tweet = MagicMock(
            text="@SC2Sbot https://t.co/eDJ2jx2I4u",
        )
        tweet.entities = {
            "urls": [
                {
                    "url": "https://t.co/eDJ2jx2I4u",
                    "expanded_url": "http://SinOsc.ar",
                    "display_url": "SinOsc.ar",
                }
            ]
        }
        self.assertEqual(
            self.twitter_bot._convert_urls_to_sc_code(tweet),
            "@SC2Sbot SinOsc.ar",
        )

    def test_filter_synth_def(self):
        # name at the beginning
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(
                MagicMock(text="@sc2sbot {SinOsc.ar}", mentions={})
            ),
            "{SinOsc.ar}",
        )

        # no name (although this should not happen)
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(
                MagicMock(text="{SinOsc.ar}", mentions={})
            ),
            "{SinOsc.ar}",
        )

        # name at the end
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(
                MagicMock(text="SinOsc.ar @sc2sbot", mentions={})
            ),
            "SinOsc.ar",
        )

        # name capitalizing
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(
                MagicMock(text="@SC2Sbot {SinOsc.ar}", mentions={})
            ),
            "{SinOsc.ar}",
        )

        # trailing whitespaces
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(
                MagicMock(text="@sc2sbot  {SinOsc.ar} ", mentions={})
            ),
            "{SinOsc.ar}",
        )

    def test_combined_tweet_replace(self):
        tweet = MagicMock(
            text="@SC2Sbot https://t.co/eDJ2jx2I4u",
        )
        tweet.entities = {
            "urls": [
                {
                    "url": "https://t.co/eDJ2jx2I4u",
                    "expanded_url": "http://SinOsc.ar",
                    "display_url": "SinOsc.ar",
                }
            ]
        }

        self.assertEqual(self.twitter_bot._filter_out_synth_def(tweet), "SinOsc.ar")
