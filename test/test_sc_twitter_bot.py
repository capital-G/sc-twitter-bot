from unittest import TestCase
from unittest.mock import MagicMock

from sc_twitter_bot.sc_twitter_bot import TwitterBot


class TwitterBotTestCase(TestCase):
    def setUp(self) -> None:
        self.twitter_bot = TwitterBot(
            consumer_key='',
            consumer_secret='',
            access_token_key='',
            access_token_secret='',
            do_login=False,
        )

    def test_convert_urls_to_sc_code(self):
        tweet = MagicMock(
            text='@SC2Sbot https://t.co/eDJ2jx2I4u',
        )
        tweet.entities = {
            'urls': [{
                'url': 'https://t.co/eDJ2jx2I4u',
                'expanded_url': 'http://SinOsc.ar',
                'display_url': 'SinOsc.ar',
            }]}
        self.assertEqual(
            self.twitter_bot._convert_urls_to_sc_code(tweet),
            '@SC2Sbot SinOsc.ar',
        )

    def test_filter_synth_def(self):
        # name at the beginning
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(MagicMock(text='@sc2sbot {SinOsc.ar}', mentions={})),
            '{SinOsc.ar}'
        )

        # no name (although this should not happen)
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(MagicMock(text='{SinOsc.ar}', mentions={})),
            '{SinOsc.ar}',
        )

        # name at the end
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(MagicMock(text='SinOsc.ar @sc2sbot', mentions={})),
            'SinOsc.ar'
        )

        # name capitalizing
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(MagicMock(text='@SC2Sbot {SinOsc.ar}', mentions={})),
            '{SinOsc.ar}',
        )

        # trailing whitespaces
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(MagicMock(text='@sc2sbot  {SinOsc.ar} ', mentions={})),
            '{SinOsc.ar}',
        )

    def test_combined_tweet_replace(self):
        tweet = MagicMock(
            text='@SC2Sbot https://t.co/eDJ2jx2I4u',
        )
        tweet.entities = {
            'urls': [{
                'url': 'https://t.co/eDJ2jx2I4u',
                'expanded_url': 'http://SinOsc.ar',
                'display_url': 'SinOsc.ar',
            }]}

        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(tweet),
            'SinOsc.ar'
        )

    def test_real_life_example(self):
        tweet = MagicMock(
            text='@SC2Sbot  { https://t.co/355mI9rrLK(https://t.co/YeyelSXZsz(200, 0.1), https://t.co/eDJ2jx2I4u(… https://t.co/P8VnqUvTTd',
            entities={
                'urls': [
                    {'url': 'https://t.co/355mI9rrLK', 'expanded_url': 'http://RLPF.ar', 'display_url': 'RLPF.ar', 'indices': [12, 35]},
                    {'url': 'https://t.co/YeyelSXZsz', 'expanded_url': 'http://Saw.ar', 'display_url': 'Saw.ar', 'indices': [36, 59]},
                    {'url': 'https://t.co/eDJ2jx2I4u', 'expanded_url': 'http://SinOsc.ar', 'display_url': 'SinOsc.ar', 'indices': [71, 94]},
                    {'url': 'https://t.co/P8VnqUvTTd', 'expanded_url': 'https://twitter.com/i/web/status/1318694051760275456', 'display_url': 'twitter.com/i/web/status/1…', 'indices': [97, 120]},
            ]}
        )
        self.assertEqual(
            self.twitter_bot._filter_out_synth_def(tweet),
            '{ http://RLPF.ar(http://Saw.ar(200, 0.1), http://SinOsc.ar(http://XLine.kr(0.7, 300, 20), 0, 3600, 4000), 0.2) }'
        )
