# Supercollider Twitter Bot

[![pre-commit](https://github.com/capital-G/sc-twitter-bot/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/capital-G/sc-twitter-bot/actions/workflows/pre-commit.yml)

A Twitter bot which replies with generated music from sended SynthDefs.

## Run tests

```shell
python -m unittest
```

## What does Supercollider do?

* Import and convert a SynthDef to an `osc` file via a [Score](https://doc.sccode.org/Classes/Score.html)
  so it can be played back in non realtime.

  ```shell
  sclang <path_to_file>
  ```

* Convert an `osc` file to audio via `sysynth` by calling

  ```shell
  scsynth -N <path_to_osc_file> _ <path_to_output_file> 48000 WAV int24
  ```

  where `_` is the placeholder for our non existing input file.
