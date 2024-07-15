import os
import subprocess
import glob

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from ..logger import Logger as _Logger

_Siril = Siril()  # type: ignore
sirilWrapper = Wrapper(_Siril)  # type: ignore

Logger = _Logger(__name__)

"""
TODO: Use GPhoto2 to get supported ISOs
"""
ISOS = [
    100, 125, 160, 200, 250, 320, 400, 500, 640, 800,
    1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000, 6400
]


class Camera():
    def __init__(self):
        self.sirilApp = _Siril
        self.siril = sirilWrapper
        self.logger = Logger

        self.model = self.get_model()
        self.logger.info(f"Camera model: {self.model}")
        self.iso = self.get_iso()
        self.logger.info(f"Camera ISO: {self.iso}")

        self.sirilApp.Open()
        self.siril.set16bits()
        self.siril.setext(os.environ['FITS_EXTENSION'])

    def close(self):
        self.sirilApp.Close()

    def _exec(self, cmd):
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        return (proc.stdout.split('\n'), proc.stderr.split('\n'))

    def get_model(self):
        self.logger.info("Getting camera model")
        cmd = ['gphoto2', '--summary']

        (stdout, _) = self._exec(cmd)

        for line in stdout:
            if "Model: " in line:
                return line\
                    .replace('Model: ', '')\
                    .strip()\
                    .replace(' ', "_")

    def get_iso(self):
        self.logger.info("Getting camera ISO")
        cmd = ['gphoto2', '--get-config', 'iso']

        (stdout, _) = self._exec(cmd)

        for line in stdout:
            if "Current: " in line:
                return line.replace('Current:', '').strip()

    def set_iso(self, iso: int):
        self.logger.info(f"Setting camera ISO to: {iso}")
        cmd = ['gphoto2', '--set-config', f'iso={iso}']
        self._exec(cmd)

    def capture_bias(self, iso: int = None, frames: int = 1):
        self.logger.info(f"Capturing bias frame")
        cmd = ['gphoto2',
               '--set-config', f'iso={iso}',
               '--set-config', 'shutterspeed=1/4000',
               '--set-config-index', 'picturestyle=1',
               f"--frames={frames}",
               f"--interval=1",
               '--filename', f"{os.environ['BIAS_LIBRARY']}/raw/{self.model}_{iso}_bias_%n.%C",
               '--capture-image-and-download',
               '--force-overwrite'
               ]
        self.logger.info(' '.join(cmd))
        self._exec(cmd)

    def stack(self, iso: int):
        self.siril.cd(f"{os.environ['BIAS_LIBRARY']}/raw")

        self.siril.convert(
            f"{self.model}_{iso}_bias", **{
                "out": f"{os.environ['BIAS_LIBRARY']}/raw",
                "fitseq": True
            }
        )

        self.siril.stack(f"{self.model}_{iso}_bias", **{
            "out": f"{self.model}_{iso}_stacked_bias",
            "type": "rej",
            'sigma_low': "3",
            'sigma_high': "3",
            'norm': 'no',
            'rejection_type': "w"
        })

        self.logger.info(f"Bias Frames Stacked for ISO: {iso}")

    def capture_master_biases(self, isos: list = None, frames: int = 30):
        """
        isos: List of ISOs to capture biases for
        frames: Number of bias frames to capture (30-60)
        """
        _isos = isos if isos else ISOS

        for iso in _isos:
            # Capture & Stack Biases
            self.capture_bias(iso=iso, frames=frames)
            self.stack(iso=iso)

            #  Move Stacked Bias to Master Library Biases Folder
            os.rename(
                f"{os.environ['BIAS_LIBRARY']}/raw/{self.model}_{iso}_stacked_bias.{os.environ['FITS_EXTENSION']}",
                f"{os.environ['BIAS_LIBRARY']}/{self.model}/biases/{self.model}_{iso}_stacked_bias.{os.environ['FITS_EXTENSION']}"
            )

            # Remove RAW and Process Files
            for f in glob.glob(f"{os.environ['BIAS_LIBRARY']}/raw/*"):
                os.remove(f)
