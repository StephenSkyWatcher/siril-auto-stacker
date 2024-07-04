from pathlib import Path
from pysiril.wrapper import *
from pysiril.siril import *
from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class SirilWrapper:
    def __init__(self, working_dir: str, biases_library: str = None) -> None:
        self.app = Siril()  # type: ignore
        self.siril = Wrapper(self.app)  # type: ignore
        self.working_dir = working_dir
        self.biases_library = biases_library
        self.fits_extension = "fit"
        self.logger = Logger

        if (biases_library is not None):
            Path(self.biases_library).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Biases Library: {biases_library}")

    def start(self):
        self.logger.info("Starting Siril")
        self.app.Open()
        self.siril.set16bits()
        self.siril.setext(self.fits_extension)
        self.siril.cd(self.working_dir)
        self.logger.info("Siril Started")

    def stop(self):
        self.logger.info("Closing Siril")
        self.app.Close()
        self.logger.info("Siril Closed")
