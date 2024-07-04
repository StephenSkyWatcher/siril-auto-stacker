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


class Biases:
    stacked_file = None

    def __init__(self,
                 SirilWrapper,
                 name: str = os.environ['BIASES_NAME'] or "bias",
                 dir: str = os.environ['BIASES_DIR_NAME'] or "biases",
                 process_dir: str = os.environ['PROCESS_DIR_NAME'] or "process",
                 stacked_prefix: str = os.environ['BIASES_STACKED_PREFIX'] or "stacked_",
                 ) -> None:

        self.logger = Logger

        self.siril = SirilWrapper.siril
        self.working_dir = SirilWrapper.working_dir
        self.fits_extension = SirilWrapper.fits_extension
        self.library = SirilWrapper.biases_library

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
            self.logger.info(f"{self.name} Stacked")
            self.load_stacked_file()
            self.siril.autostretch()
            self.siril.savejpg(f"{self.stacked_name}-preview")
            self.logger.info(f"Saved {self.name} Preview")
            self.stacked_file = f"{self.working_dir}/{self.dir}/{self.stacked_name}.{self.fits_extension}"
        except Exception as e:
            self.logger.error(f"Failed to Stack {self.name}", e)
            return

    def load_stacked_file(self):
        if not self.__stacked_file_exists():
            self.logger.error("Stacked File does not exist")
            raise Exception("Stacked File does not exist")
        self.cd_process_dir()
        self.siril.load(f"{self.stacked_name}.{self.fits_extension}")

    def get_master_library_filename(self):
        try:
            with ExifToolHelper() as exif:
                full_biases_path = f"{self.working_dir}/{self.dir}"
                first_bias_file = f"{full_biases_path}/{os.listdir(full_biases_path)[0]}"
                tags = ["EXIF:ISO", "Make", "Model"]
                tags = exif.get_tags(files=first_bias_file, tags=tags)[0]
                iso = tags.get('EXIF:ISO')
                model = tags.get('EXIF:Model')
                master_library_name = f"{model} {iso} {self.stacked_name}".replace(
                    " ", "_")
                return master_library_name
        except Exception as e:
            self.logger.error("Failed to get Master Library File", e)
            raise e

    def get_master_library_file(self):
        try:
            file = f"{self.library}/{self.get_master_library_filename()}.{self.fits_extension}"
            if os.path.isfile(file):
                return file
        except Exception as e:
            self.logger.error("Failed to get Master Library File", e)
            raise e

    def get_stacked_file(self) -> str:
        return f"{self.working_dir}/{self.dir}/{self.process_dir}/{self.stacked_name}.{self.fits_extension}"

    def save_to_master_library(self):
        self.logger.info("Saving Master Bias to Library")
        try:
            self.load_stacked_file()
            library_filename = self.get_master_library_filename()
            self.siril.cd(self.library)
            self.siril.save(library_filename)
            self.logger.info("Master Bias Saved to Library")
        except Exception as e:
            self.logger.error("Failed to save Master Bias to Library", e)
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
