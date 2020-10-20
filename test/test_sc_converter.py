import os
from unittest import TestCase

from sc_twitter_bot.sc_converter import SuperColliderConverter, ConverterException


class SupercolliderConverterTestCase(TestCase):
    def setUp(self):
        self.sc_converter = SuperColliderConverter()

    def test_synth_def(self, test_file: str = 'test.wav', delete: bool = True):
        try:
            self.sc_converter.playback_synthdef('SinOsc.ar(100)', test_file)
            self.assertTrue(os.path.isfile(test_file))
        finally:
            if delete:
                os.remove(test_file)

    def test_synth_def_with_braces(self, test_file: str = 'test.wav', delete: bool = False):
        try:
            self.sc_converter.playback_synthdef('{SinOsc.ar(100)}', test_file)
            self.assertTrue(os.path.isfile(test_file))
        finally:
            if delete:
                os.remove(test_file)

    def test_invalid_sc_code(self):
        with self.assertRaises(ConverterException):
            self.sc_converter.playback_synthdef('{ this is not a valid command', 'test.wav', timeout=3)
            self.assertFalse(os.path.isfile('test.wav'))

    def test_fail_setup(self):
        with self.assertRaises(ConverterException):
            SuperColliderConverter(
                scsynth_path='foo',
                sclang_path='bar',
            )
