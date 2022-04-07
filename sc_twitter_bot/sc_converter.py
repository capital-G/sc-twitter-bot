import subprocess
import tempfile
import os
import time
from datetime import datetime
from string import Template
from typing import Optional
import logging

log = logging.getLogger(__name__)


class ConverterException(Exception):
    pass


class SuperColliderConverter:
    def __init__(
        self,
        sclang_path: Optional[str] = None,
        scsynth_path: Optional[str] = None,
        blueprint_file_path: Optional[str] = None,
    ):
        self.sclang_path = sclang_path or os.environ.get("SCLANG_PATH") or "sclang"
        self.scsynth_path = scsynth_path or os.environ.get("SCSYNTH_PATH") or "scsynth"
        self._blueprint_file_path = blueprint_file_path or os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "blueprint.sc"
        )

        try:
            subprocess.check_output([self.sclang_path, "-h"])
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise ConverterException(
                f"Please check sclang path or install supercollider! {e}"
            )

        try:
            subprocess.check_output([self.scsynth_path, "-v"])
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise ConverterException(
                f"Please check scsynth path or install supercollider! {e}"
            )

        with open(self._blueprint_file_path, "r") as f:
            self._sc_blueprint = f.read()

    def _sc_to_osc_file(
        self,
        synth_def: str,
        osc_file_path: str,
        timeout: int = 10,
        duration: float = 10.0,
        **kwargs,
    ):
        """
        For some reason we cannot use the simple `subprocess.check_output` here as it will
        keep waiting for user input although the process kills itself when called from shell.
        This causes in some pretty hacky stuff now, sorry.

        :param synth_def:
        :param osc_file_path:
        :return:
        """
        sc_template = Template(self._sc_blueprint).substitute(
            osc_path=osc_file_path, synth_def=synth_def, duration=f"{duration:.1f}"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".sc") as sc_file:
            log.debug(f"Write SC template to {sc_file.name}")
            sc_file.write(sc_template)
            sc_file.flush()

            start_time = datetime.now()
            log.debug(f"Starting conversion to OSC of {synth_def}")
            p = subprocess.Popen(
                [self.sclang_path, sc_file.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=False,
            )
            try:
                p.wait(timeout)
            except subprocess.TimeoutExpired:
                log.debug("Could not receive sclang exit code in time")
            finally:
                p.kill()

            if os.path.getsize(sc_file.name) < 5:
                raise ConverterException(
                    f"Could not convert {synth_def} to OSC - syntax error?"
                )

    def _osc_to_wav(
        self,
        osc_file: str,
        wav_file: str,
        sample_rate: int = 48000,
        header_format: str = "WAV",
        sample_format: str = "int24",
        num_channels: int = 1,
        **kwargs,
    ):
        log.debug(f"Start converting {osc_file} to {wav_file}")
        start_time = datetime.now()
        try:
            subprocess.check_output(
                [
                    self.scsynth_path,
                    "-N",
                    osc_file,
                    "_",
                    wav_file,
                    str(sample_rate),
                    header_format,
                    sample_format,
                    "-o",
                    str(num_channels),
                ]
            )
        except subprocess.CalledProcessError as e:
            raise ConverterException(f"Failed convert {osc_file} to {wav_file}: {e}")
        log.info(
            f"Successfully converted {osc_file} to {wav_file} in {(datetime.now() - start_time).seconds} seconds"
        )

    def playback_synthdef(self, synth_def: str, output_file_path: str, **kwargs):
        """
        Converts a supercollider SynthDef to a wav file by playing the SynthDef.
        For this we first convert the SynthDef to a OSC score via ``sclang`` and then convert
        this OSC blob to a wav file with ``scsynth``.

        :param synth_def: SuperCollider SynthDef, e.g.
            .. code-block:: supercollider

                {SinOsc.ar}

        :param output_file_path: Path were the `.wav` file will be created.
        :param kwargs: Check :func:`~SuperColliderConverter._osc_to_wav` for further parameters.
        :return:
        """
        with tempfile.NamedTemporaryFile(suffix=".osc") as osc_file:
            self._sc_to_osc_file(synth_def, osc_file.name, **kwargs)
            self._osc_to_wav(osc_file.name, output_file_path, **kwargs)
