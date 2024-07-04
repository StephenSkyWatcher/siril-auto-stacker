import math
from pysiril.wrapper import *
from pysiril.siril import *
from matplotlib import pyplot as plt
import cv2 as cv
from pathlib import Path
import os
from exiftool import ExifToolHelper
import subprocess
from ..astrometry.wcs import get_center_coords
from astropy import units as u
from astropy.coordinates import (ICRS, SkyCoord, get_icrs_coordinates)
from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class Darks:
    def __init__(self,
                 SirilWrapper,
                 name: str = os.environ['DARKS_NAME'] or "dark",
                 dir: str = os.environ['DARKS_DIR_NAME'] or "darks",
                 process_dir: str = os.environ['PROCESS_DIR_NAME'] or "process",
                 stacked_prefix: str = os.environ['DARKS_STACKED_PREFIX'] or "stacked_",
                 ) -> None:

        self.logger = Logger

        self.siril = SirilWrapper.siril
        self.working_dir = SirilWrapper.working_dir
        self.fits_extension = SirilWrapper.fits_extension

        self.name = name
        self.dir = dir

        self.process_dir = process_dir
        self.stacked_name = f"{stacked_prefix}{name}"
        self.__validate_dir()

    def cd_working_dir(self):
        self.siril.cd(self.working_dir)

    def cd_dir(self):
        self.cd_working_dir()
        self.siril.cd(self.dir)

    def cd_process_dir(self):
        self.cd_dir()
        self.siril.cd(self.process_dir)

    def convert(self):
        self.logger.info(f"Converting {self.name}")
        self.cd_dir()
        self.siril.convert(self.name, out=self.process_dir, fitseq=True)
        self.logger.info(f"{self.name} Converted")

    def stack(self):
        try:
            self.logger.info(f"Stacking {self.name}")
            self.cd_process_dir()
            self.siril.stack(
                self.name,
                type='rej',
                sigma_low=3,
                sigma_high=3,
                norm='no',
                out=self.stacked_name
            )
            self.logger.info(f"Stacked {self.name}")
            self.load_stacked_file()
            self.siril.autostretch()
            self.siril.savejpg(f"{self.stacked_name}-preview")
            self.logger.info(f"Saved {self.name} Preview")
        except Exception as e:
            self.logger.error(f"Failed to Stack {self.name}", e)
            return

    def load_stacked_file(self):
        if not self.__stacked_file_exists():
            self.logger.error("Stacked File does not exist")
            raise Exception("Stacked File does not exist")
        self.cd_process_dir()
        self.siril.load(f"{self.stacked_name}.{self.fits_extension}")

    def get_stacked_file(self) -> str:
        if (self.__stacked_file_exists()):
            return f"{self.working_dir}/{self.dir}/{self.process_dir}/{self.stacked_name}.{self.fits_extension}"
        else:
            self.logger.error("Stacked File does not exist")
            return

    def __valid_dir(self) -> bool:
        return os.path.exists(self.dir) and len(os.listdir(self.dir)) != 0

    def __validate_dir(self):
        if not self.__valid_dir():
            self.logger.error(
                f"Directory {self.dir} does not exist or is empty")
            raise Exception(
                f"Directory {self.dir} does not exist or is empty")

    def __stacked_file_exists(self) -> bool:
        return os.path.isfile(f"{self.working_dir}/{self.dir}/{self.process_dir}/{self.stacked_name}.{self.fits_extension}")
