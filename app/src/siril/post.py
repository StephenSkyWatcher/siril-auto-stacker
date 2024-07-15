import os
from pathlib import Path
import subprocess

from astropy import units as u
from astropy.coordinates import SkyCoord

from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class Post:
    wd: str = None
    name: str = None

    def __init__(self,
                 SirilWrapper,
                 ) -> None:

        self.logger = Logger

        self.siril = SirilWrapper.siril
        self.working_dir = SirilWrapper.working_dir
        self.fits_extension = SirilWrapper.fits_extension
        self.preprocess_prefix = SirilWrapper.preprocess_prefix
        self.registered_prefix = SirilWrapper.registered_prefix
        self.target_ra = SirilWrapper.target_ra
        self.target_dec = SirilWrapper.target_dec

    def load(self, file):
        #  TODO: Needs work and error handling
        self.siril.cd(self.working_dir)
        relative_file_dir = os.path.normpath(
            os.path.dirname(file)).replace(f"{self.working_dir}/", '')
        self.siril.cd(relative_file_dir)

        [loaded] = self.siril.load(file)
        if loaded:
            self.wd = os.path.dirname(file)
            self.name = Path(file).stem

    def save(self, name=None):
        self.siril.cd(self.wd)
        self.siril.save(f"{self.name if name is None else name}-preview")

    def autostretch(self):
        self.siril.autostretch()
        self.logger.info(f"Autostretch Completed")

    def rmgreen(self):
        self.siril.rmgreen()
        self.logger.info(f"Green Removed")

    def starnet(self):
        self.logger.info(f"Running Starnet++")
        res = self.siril.starnet(
            stretch=False,
            upscale=False,
            stride=None,
            nostarmask=False
        )
        self.logger.info('starnet', res)
        self.logger.info(f"Starnet++ Completed")

    def ght(self):
        self.logger.info("Starting Generalized Histogram Transformation")
        self.siril.ght(3.5, 0, 0, 0.3, 1, independent=True,
                       human=True, even=True)

    def solve(self, file, stretch=False, ra=None, dec=None):
        self.logger.info(f"Plate Solving: {file}")
        self.siril.cd(os.path.dirname(file))
        self.siril.load(file)

        if stretch:
            self.siril.autostretch()

        self.siril.platesolve(
            platesolve=True,
            center_coords=f"{ra},{dec}",
        )

        self.siril.save(file)

    def denoise(self, file, gpu=False):
        self.logger.info(f"Denoising: {file}")
        gradient_cmd = [
            'graxpert',
            file,
            "-cli",
            "-gpu", "true" if gpu else "false",
            "--command", "denoising"
        ]
        subprocess.run(gradient_cmd)

        self.logger.info("Denoising Complete")
        self.logger.info(
            f"THE DENOISING FINAL IMAGE PATH: {Path(file).stem}_GraXpert.fits")
        # self.siril.load(f"{Path(file).stem}_GraXpert.fits")

    def remove_gradient(self, file: str, gpu=False):
        gradient_cmd = [
            "graxpert",
            file,
            "-cli",
            "-correction", "Subtraction",
            "-smoothing", "0.1",
            "-bg",
            "-gpu", "true" if gpu else "false",
            "--command", "background-extraction"
        ]
        self.logger.info(f"Running GraXpert Background Extraction")
        subprocess.run(gradient_cmd)
        self.logger.info(f"Gradient Removed")

    def final(self, file, stretch=True, remove_work=True, denoise=False, star_stretch=True, extra_star_denoise=False, ra=None, dec=None, ):
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
        self.siril.cd(os.path.dirname(file))
        self.siril.load(os.path.basename(file))

        """
        Autostretch
        """
        if stretch:
            self.logger.info("Auto stretching")
            self.siril.autostretch()
            self.siril.save(os.path.basename(file))
            self.siril.load(os.path.basename(file))

        """
        Plate Solve
        """
        self.logger.info("Plate Solving")
        self.siril.load(os.path.basename(file))
        try:
            self.solve(file, ra=ra, dec=dec)
        except Exception as e:
            self.logger.warn(
                f"Failed to run Plate Solving. Moving on...")
            pass

        """
        Photometric Color Calibration
        """
        self.logger.info("Running Photometric Color Calibration")
        self.siril.save(os.path.basename(file))
        self.siril.load(os.path.basename(file))

        try:
            self.siril.pcc(
                center_coords=f"{ra},{dec}",
                platesolve=False,
                # pixelsize=1.85,
                # focal=340.91
                # limitmag=-5
            )
            self.save(os.path.basename(file))
        except Exception as e:
            self.logger.warn(
                f"Failed to run Photometric Color Calibration. Moving on...")
            pass

        """
        Starnet++
        """
        self.starnet()
        starless = f"starless_{Path(file).stem}"
        starmask = f"starmask_{Path(file).stem}"
        self.logger.debug(f"Starless: {starless}")
        self.logger.debug(f"Starmask: {starmask}")

        if not f"{os.path.dirname(file)}/{os.path.isfile(starless)}.{os.environ['FITS_EXTENSION']}" or not f"{os.path.dirname(file)}/{os.path.isfile(starmask)}.{os.environ['FITS_EXTENSION']}":
            self.logger.debug(
                f"{os.path.dirname(file)}/{os.path.isfile(starless)}.{os.environ['FITS_EXTENSION']}")
            self.logger.debug(
                f"{os.path.dirname(file)}/{os.path.isfile(starmask)}.{os.environ['FITS_EXTENSION']}")

            raise Exception(
                f"Cannot find starless and starmask files")

        """
        Stars Processing
        """
        self.siril.load(starmask)

        if star_stretch:
            # ASINH Stretch
            self.logger.info(f"ASINH Stretch: 0 // 0.2 on Stars")
            [completed] = self.siril.asinh(1, human=True, offset=0.2)
            if completed is not True:
                raise Exception("ASINH Stretch on Stars Failed")

        # Denoise
        self.logger.info(f"Denoising Stars")
        [completed] = self.siril.denoise(
            mod=1, nocosmetic=False, da3d=extra_star_denoise)
        if completed is not True:
            raise Exception("Denoising Stars Failed")

        self.logger.info(f"Saving: {starmask}")
        self.siril.save(starmask)

        """
        Starless Processing
        """
        full_starless_path = f"{os.path.dirname(file)}/{starless}.fit"
        starless_graxpert_path = f"{os.path.dirname(file)}/{starless}_GraXpert.fits"

        #  Denoise
        if denoise:
            #  Remove Gradient
            self.logger.info(f"Removing Gradient with GraXpert")
            self.remove_gradient(full_starless_path)
            #  Denoise
            self.logger.info(f"Denoising with GraXpert")
            self.denoise(starless_graxpert_path)
            self.logger.debug(starless_graxpert_path)
        else:
            #  Remove Gradient
            self.logger.info(f"Removing Gradient with GraXpert")
            self.logger.debug(full_starless_path)
            self.remove_gradient(full_starless_path)

        self.siril.load(starless_graxpert_path)

        # ASINH Stretch
        self.logger.info(f"ASINH Stretch: 0 // 0.2 on Stars")
        [completed] = self.siril.asinh(1, human=True, offset=0.18)
        if completed is not True:
            raise Exception("ASINH Stretch on Stars Failed")

        self.logger.info(f"Saving: {starless}")
        self.siril.save(starless)

        """
        Star Recomposition
        """
        self.logger.info(
            f"Combining Starless and Starmask with PixelMath: Starless: {starless}.fit   Stars: {starmask}.fit")
        self.siril.pm(
            expression=f"${starless}.fit$ * 0.5 + ${starmask}.fit$ * 0.5",
            rescale=True,
            low=0.0,
            high=0.9
        )

        postprocessed = f"{Path(file).stem}_postprocessed"
        self.logger.info(f"Saving: { postprocessed }")
        self.siril.save(postprocessed)

        """
        Final
        """
        final_file = f"{os.path.dirname(file)}/{postprocessed}.{os.environ['FITS_EXTENSION']}"

        if remove_work:
            try:
                os.remove(f"{starless_graxpert_path}")
            except:
                pass

        self.logger.info(f"Final Processing Complete: {final_file}")

    def hubble_pallette(self, file):
        self.logger.info(f"Saving Hubble Pallette")
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

    # def preview(self, file, rmgreen=True, pcc=True, autostretch=True, starnet=True, astro=False, type="jpg"):
    #     self.logger.info(f"Saving Previews")
    #     self.siril.cd(os.path.dirname(file))
    #     [loaded] = self.siril.load(os.path.basename(file))

    #     self.logger.info(f"loaded {loaded}")

    #     if not loaded:
    #         self.logger.error(f"Could not load {file}")
    #         raise Exception(f"Could not load {file}")

    #     if rmgreen:
    #         self.logger.info(f"Removing Green Noise")
    #         self.siril.rmgreen()
    #         self.logger.info(f"Green Noise Removed")

    #     if autostretch:
    #         self.logger.info(f"Running Autostretch")
    #         self.siril.autostretch()
    #         self.logger.info(f"Autostretch Complete")

    #     if pcc:
    #         try:
    #             self.logger.info(f"Running Photometric Color Calibration")
    #             ra = self.target_ra
    #             dec = self.target_dec

    #             if ra and dec:
    #                 self.siril.pcc(
    #                     limitmag=0,
    #                     center_coords=f"{ra},{dec}",
    #                     platesolve=False,
    #                     catalog=f"{self.results_dir}/{self.light_stacked_name}/{self.light_stacked_name}.wcs")
    #                 self.logger.info(f"Photometric Color Calibration Complete")
    #             else:
    #                 self.logger.error(
    #                     f"Failed to run Photometric Color Calibration. No Target Coordinates")

    #         except Exception as e:
    #             self.logger.error(
    #                 f"Failed to run Photometric Color Calibration", e)
    #             pass

    #     if type == 'jpg':
    #         self.siril.savejpg(Path(file).stem)
    #     else:
    #         self.siril.savetif(Path(file).stem)

    #     self.logger.info(f"Saved Previews")
