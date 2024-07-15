import os
from pathlib import Path
import subprocess

from astropy import units as u
from astropy.coordinates import SkyCoord

from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class PostProcess:
    logger: _Logger = None

    def __init__(self, SirilWrapper, frame) -> None:
        self.SirilWrapper = SirilWrapper
        self.logger = Logger
        self.frame = frame
        self.loaded = None
        self.starless = None
        self.starmask = None

    def load(self, file: str):
        self.logger.info(f"Loading {file} to be processed....")
        self.SirilWrapper.siril.cd(os.path.dirname(file))
        self.SirilWrapper.siril.load(Path(file).stem)
        self.SirilWrapper.siril.save(f"{Path(file).stem}.bak")
        self.loaded = file
        self.logger.info(f"Loaded {file}")
        return self

    def remove_green_noise(self):
        self.logger.info(f"Removing Green Noise....")
        self.assert_loaded()
        self.SirilWrapper.siril.rmgreen()
        self.logger.info(f"Green Noise Removed")
        return self

    def autostretch(self):
        self.logger.info(f"Applying an Autostretch...")
        self.assert_loaded()
        self.SirilWrapper.siril.autostretch()
        self.logger.info(f"Autostretch Completed")
        return self

    def starnet(self):
        self.logger.info(f"Running Starnet++")
        self.assert_loaded()

        [success] = self.SirilWrapper.siril.starnet(
            stretch=False,
            upscale=False,
            stride=None,
            nostarmask=False
        )

        if success is True:
            full_process_dir_path = f"{self.SirilWrapper.working_dir}/{self.frame.dir}/{self.frame.process_dir}"
            self.starless = f"{full_process_dir_path}/starless_{Path(self.loaded).stem}"
            self.starmask = f"{full_process_dir_path}/starmask_{Path(self.loaded).stem}"

            self.logger.info(f"Starnet++ Completed")
            return self
        else:
            raise Exception("Starnet++ Failed")

    def ght(self,
            factor: float = 3.5,
            intensity: float = 0,
            shadow_protection: float = 0,
            symmetry: float = 0.3,
            highlight_protection: float = 1,
            independent: bool = True,
            human: bool = True,
            even: bool = True
            ):

        self.logger.info("Starting Generalized Histogram Transformation")
        self.assert_loaded()

        ght_params = {
            'D': factor,
            'B': intensity,
            'LP': shadow_protection,
            'SP': symmetry,
            'HP': highlight_protection,
            'independent': independent,
            'human': human,
            'even': even
        }

        self.SirilWrapper.siril.ght(**ght_params)
        return self

    def equalize(self, cliplimit=2, tileSize=8):
        self.assert_loaded()
        self.SirilWrapper.siril.clahe(cliplimit=cliplimit, tileSize=tileSize)
        return self

    def denoise(self, gpu=False):
        """
        Denoising the image can take a long time
        """
        self.assert_loaded()
        self.logger.info(f"Denoising: {self.loaded}")
        gradient_cmd = [
            'graxpert',
            self.loaded,
            "-cli",
            "-gpu", "true" if gpu else "false",
            "--command", "denoising"
        ]

        subprocess.run(gradient_cmd)

        self.logger.info("Denoising Complete")
        self.logger.info(
            f"THE DENOISING FINAL IMAGE PATH: {Path(self.loaded).stem}_GraXpert.fits")
        self.SirilWrapper.siril.load(f"{Path(self.loaded).stem}_GraXpert.fits")
        self._save()
        os.remove(
            f"{os.path.dirname(self.loaded)}/{Path(self.loaded).stem}_GraXpert.fits")
        return self

    def remove_gradient(self, gpu=False):
        self.logger.info(f"Running GraXpert Background Extraction")
        self.assert_loaded()
        gradient_cmd = [
            "graxpert",
            self.loaded,
            "-cli",
            "-correction", "Subtraction",
            "-smoothing", "0.1",
            "-bg",
            "-gpu", "true" if gpu else "false",
            "--command", "background-extraction"
        ]
        subprocess.run(gradient_cmd)
        self.logger.info(f"Gradient Removed")
        self.SirilWrapper.siril.load(f"{Path(self.loaded).stem}_GraXpert.fits")
        self._save()
        os.remove(
            f"{os.path.dirname(self.loaded)}/{Path(self.loaded).stem}_GraXpert.fits")

        return self

    def solve(self,
              ra,
              dec,
              force=True,
              localasnet=False,
              pixelsize=None,
              focal=None,
              downscale=True,
              noflip=False,
              limitmag=None,
              catalog=None,
              ):

        self.logger.info(f"Plate Solving")

        self.assert_loaded()

        if not ra or not dec:
            self.logger.error("RA and DEC are required to solve")
            return self

        if pixelsize is None:
            # TODO: Try meta data on image
            pixelsize = None
        if focal is None:
            # TODO: Try meta data on image
            focal = None

        platesolve_params = {
            'localasnet': localasnet,
            'platesolve': force,
            'center_coords': f"{ra},{dec}",
            'pixelsize': pixelsize,
            'focal': focal,
            'downscale': downscale,
            'noflip': noflip,
            'limitmag': limitmag,
            'catalog': catalog,
        }

        self.SirilWrapper.siril.platesolve(**platesolve_params)
        self.SirilWrapper.siril.save(self.loaded)
        self.SirilWrapper.siril.load(self.loaded)
        self.logger.info(f"Plate Solving Completed")
        return self

    def photometric_color_calibration(self, ra, dec):
        self.logger.info(f"Running Photometric Color Calibration")
        self.SirilWrapper.siril.pcc(
            center_coords=f"{ra},{dec}",
            platesolve=False,
            # pixelsize=1.85,
            # focal=340.91
            # limitmag=-5
        )
        return self

    def _star_recomposition(self, starless, starmask):
        self.logger.info(
            f"Combining Starless and Starmask with PixelMath: Starless: {starless}.fit   Stars: {starmask}.fit")

        self.SirilWrapper.siril.pm(
            expression=f"${starless}.fit$ * 0.5 + ${starmask}.fit$ * 0.5",
            rescale=True,
            low=0.0,
            high=0.9
        )

    def nebula(
            self, stretch=True, remove_work=True, denoise=False,
            star_stretch=True, extra_star_denoise=False, ra=None, dec=None
    ):
        """
        Does a full processing of a stacked light frame

        Essentially, the goal is to automate doing the
        initial (repetitive) post-processing allowing me
        to get right to the fine details.

        The process is as follows:
        - Load the file
        - Autostretch (conditionally)
        - Starnet++ - to split into two files: stars and starless

        - Star Processing - Minor star reduction
            - Increase Black Point
            - Denoise (simple)

        - Starless Processing - (AI)
            - Denoise with GraXpert (This process can take a long time)
            - Remove Gradient with GraXpert
            - Generalized Histogram Transformation

        - Star Recomposition
            - Combine Starless and Starmask with PixelMath

        """
        self.assert_loaded()
        self.SirilWrapper.siril.save(f"{Path(self.loaded).stem}.nebula.bak")

        if stretch:
            self.autostretch()

        if ra and dec:
            try:
                self.solve(ra, dec)
            except Exception as e:
                self.logger.warning('Plate Solving Failed')
                pass

            try:
                self.photometric_color_calibration(ra, dec)
            except Exception as e:
                self.logger.warning('Photometric Color Calibration Failed')
                pass

        self.starnet()

        """
        Star Processing
        """
        self.SirilWrapper.siril.cd(os.path.dirname(self.starmask))
        self.SirilWrapper.siril.load(Path(self.starmask).stem)
        self.SirilWrapper.siril.save(f"{Path(self.starmask).stem}.bak")

        if star_stretch:
            # ASINH Stretch
            self.logger.info(f"ASINH Stretch: 0 // 0.2 on Stars")
            [completed] = self.SirilWrapper.siril.asinh(
                1, human=True, offset=0.2)
            if completed is not True:
                raise Exception("ASINH Stretch on Stars Failed")

        # Denoise
        self.logger.info(f"Denoising Stars")
        [completed] = self.SirilWrapper.siril.denoise(
            mod=1, nocosmetic=False, da3d=extra_star_denoise)
        if completed is not True:
            raise Exception("Denoising Stars Failed")

        self.logger.info(f"Saving: {self.starmask}")
        self.SirilWrapper.siril.save(self.starmask)

        """
        Starless Processing
        """
        self.SirilWrapper.siril.cd(os.path.dirname(self.starless))
        self.SirilWrapper.siril.load(Path(self.starless).stem)
        self.SirilWrapper.siril.save(f"{Path(self.starless).stem}.bak")

        # Generated from running GraXpert
        starless_graxpert_path = f"{os.path.dirname(self.starless)}/{Path(self.starless).stem}_GraXpert.fits"

        #  Remove Gradient
        self.remove_gradient(self.starless)

        if denoise:
            self.denoise(starless_graxpert_path)
            self.SirilWrapper.siril.save(self.starless)

        self.SirilWrapper.siril.load(self.starless)

        # ASINH Stretch
        self.logger.info(f"ASINH Stretch: 0 // 0.2 on Background")
        [completed] = self.SirilWrapper.siril.asinh(1, human=True, offset=0.18)
        if completed is not True:
            raise Exception("ASINH Stretch on Background Failed")

        self.logger.info(f"Saving: {self.starless}")
        self.SirilWrapper.siril.save(self.starless)

        """
        Star Recomposition
        """
        self._star_recomposition(
            starless=self.starless, starmask=self.starmask)

        postprocessed = f"{Path(self.loaded).stem}_postprocessed"
        self.logger.info(f"Saving: { postprocessed }")
        self.SirilWrapper.siril.save(postprocessed)

        """
        Final
        """
        final_file = f"{self.SirilWrapper.working_dir}/{self.frame.dir}/{self.frame.process_dir}/{postprocessed}.{os.environ['FITS_EXTENSION']}"

        # if remove_work:
        #     try:
        #         os.remove(f"{starless_graxpert_path}")
        #         os.remove(self.starless)
        #         os.remove(self.starmask)
        #     except:
        #         pass

        self.logger.info(f"Final Processing Complete: {final_file}")

        return final_file

    """
    def hubble_pallette(self, file):
        self.logger.info(f"Saving Hubble Pallette")
        self.assert_loaded()
        self.siril.cd(os.path.dirname(file))
        [loaded] = self.siril.load(os.path.basename(file))

        self.logger.info(f"loaded {loaded}")

        if not loaded:
            self.logger.error(f"Could not load {file}")
            raise Exception(f"Could not load {file}")

        # self.siril.subsky(rbf=True, smooth=0.5, samples=10)
        self.siril.rmgreen()
        self.siril.autostretch()

        stem = Path(file).stem
        rgb_comp = f"{stem}-rgb"
        red = f"{stem}-red"
        green = f"{stem}-green"
        blue = f"{stem}-blue"

        self.logger.info(f"Red: {red}")
        self.logger.info(f"Green: {green}")
        self.logger.info(f"Blue: {blue}")

        self.siril.split(
            red,
            green,
            blue,
        )

        self.siril.rgbcomp(
            lum=red,
            rgb_image=None,
            red=red,
            green=red,
            blue=green,
            out=rgb_comp
        )

        self.siril.load(rgb_comp)
        self.siril.rmgreen()
        self.siril.satu(amount=1, background_factor=0)
        self.siril.save(f"{rgb_comp}-hubble")
    """

    def assert_loaded(self):
        if not self.loaded:
            raise Exception("No file loaded to process")

    def jsonmetadata(self):
        self.SirilWrapper.siril.jsonmetadata(
            self.loaded,
            stats_from_loaded=True,
            nostats=False,
            out=f"{Path(self.loaded).stem}-metadata.json"
        )
        self.SirilWrapper.siril.dumpheader()
        return self

    def preview(self, filename: str = 'preview', type: str = 'jpg'):
        self.assert_loaded()
        self.logger.info(f"Saving a preview....")

        if type == 'jpg':
            self.SirilWrapper.siril.savejpg(filename)
        if type == 'png':
            self.SirilWrapper.siril.savepng(filename)
        if type == 'tif':
            self.SirilWrapper.siril.savetif(filename)
        if type == 'tif8':
            self.SirilWrapper.siril.savetif8(filename)
        if type == 'tif32':
            self.SirilWrapper.siril.savetif32(filename)

        self.logger.info(f"Preview Saved: {filename}")
        return self

    def _save(self):
        [saved] = self.SirilWrapper.siril.save(self.loaded)
        if saved is True:
            self.logger.info(f"Saved {self.loaded}")
            self.SirilWrapper.siril.load(self.loaded)
        else:
            raise Exception(f"Failed to save {self.loaded}")
