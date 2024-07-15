from .master_library import get_library_file
import os
from typing import Optional
from .frame import Frame
from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class Session:
    def __init__(self,
                 biases: Optional[Frame],
                 darks: Optional[Frame],
                 flats: Optional[Frame],
                 lights: Optional[Frame],
                 working_dir: str,
                 multiple: bool = False
                 ):
        self.logger = Logger
        self.biases = biases
        self.darks = darks
        self.flats = flats
        self.lights = lights
        self.multiple = multiple
        #
        self.working_dir = working_dir

    def validate_supported(self, frame: Frame):
        if frame not in [self.darks, self.flats, self.lights]:
            raise Exception(
                "Multinight Calibration is not supported for this type of frame")

    def getMultiNightDirectories(self, dir):
        list = []
        for root, dirs, files in os.walk(dir):
            for d in dirs:
                if os.environ['MULTINIGHT_DIR_NAME'] in d:
                    list.append(f"{dir}{d}")
            break  # prevents descending into subfolders

        return list

    def list_directories(self, frame: Frame):
        return [f"{self.working_dir}/{frame.dir}/"] if not self.multiple else self.getMultiNightDirectories(
            f"{self.working_dir}/{frame.dir}/")

    def get_stacked_file(self, frame: Frame, night="") -> str:
        if frame is self.biases:
            return get_library_file(
                type=self.biases, light=self.lights, night=night)
        else:
            base = f"{self.working_dir}/{frame.dir}/{frame.process_dir}"

            filename_postfix = f"_{night}" if night else ""

            r_pp_name_full_filename = f"{base}/{os.environ['REGISTERED_PREFIX']}{os.environ['PREPROCESS_PREFIX']}{frame.stacked_name}{filename_postfix}.{os.environ['FITS_EXTENSION']}"
            pp_name_full_filename = f"{base}/{os.environ['PREPROCESS_PREFIX']}{frame.stacked_name}{filename_postfix}.{os.environ['FITS_EXTENSION']}"
            r_name_full_filename = f"{base}/{os.environ['REGISTERED_PREFIX']}{frame.stacked_name}{filename_postfix}.{os.environ['FITS_EXTENSION']}"
            name_full_filename = f"{base}/{frame.stacked_name}{filename_postfix}.{os.environ['FITS_EXTENSION']}"

            for f in [r_pp_name_full_filename, pp_name_full_filename, r_name_full_filename, name_full_filename]:
                self.logger.debug(f"Trying to get Stacked File: {f}")
                if (os.path.isfile(f)):
                    self.logger.debug(f"Found Stacked File: {f}")
                    return f

            raise Exception(
                "Stacked Light File does not exist. Did you run stack()?")
