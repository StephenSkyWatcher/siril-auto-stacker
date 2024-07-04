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


class FilesConfig:
    def __init__(
        self,
        working_dir=os.getcwd(),
        process_dir_name=os.environ['PROCESS_DIR_NAME'],
        biases_dir_name=os.environ['BIASES_DIR_NAME'],
        flats_dir_name=os.environ['FLATS_DIR_NAME'],
        darks_dir_name=os.environ['DARKS_DIR_NAME'],
        lights_dir_name=os.environ['LIGHTS_DIR_NAME'],
        results_dir_name=os.environ['RESULTS_DIR_NAME'],
        masters_dir_name=os.environ['MASTERS_DIR_NAME'],
        master_library_path=os.environ['MASTER_LIBRARY_PATH'],

    ) -> None:
        self.working_dir = working_dir
        self.process_dir_name = process_dir_name
        self.biases_dir_name = biases_dir_name
        self.flats_dir_name = flats_dir_name
        self.darks_dir_name = darks_dir_name
        self.lights_dir_name = lights_dir_name
        self.results_dir_name = results_dir_name
        self.masters_dir_name = masters_dir_name
        self.master_library_path = master_library_path


class StackConfig(FilesConfig):
    def __init__(
        self,
        working_dir=os.getcwd(),
        bias_conversion_name=os.environ['BIAS_CONVERSION_NAME'],
        flat_conversion_name=os.environ['FLAT_CONVERSION_NAME'],
        dark_conversion_name=os.environ['DARK_CONVERSION_NAME'],
        light_conversion_name=os.environ['LIGHT_CONVERSION_NAME'],
        bias_stacked_name=os.environ['BIAS_STACKED_NAME'],
        flat_stacked_name=os.environ['FLAT_STACKED_NAME'],
        dark_stacked_name=os.environ['DARK_STACKED_NAME'],
        light_stacked_name=os.environ['LIGHT_STACKED_NAME'],
        registered_prefix=os.environ['REGISTERED_PREFIX'],
        preprocess_prefix=os.environ['PREPROCESS_PREFIX'],
        fits_extension=os.environ['FITS_EXTENSION'],
    ) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.bias_conversion_name = bias_conversion_name
        self.flat_conversion_name = flat_conversion_name
        self.dark_conversion_name = dark_conversion_name
        self.light_conversion_name = light_conversion_name
        self.bias_stacked_name = bias_stacked_name
        self.flat_stacked_name = flat_stacked_name
        self.dark_stacked_name = dark_stacked_name
        self.light_stacked_name = light_stacked_name
        self.registered_prefix = registered_prefix
        self.preprocess_prefix = preprocess_prefix
        self.fits_extension = fits_extension
        self.biases_dir = f"{self.working_dir}/{self.biases_dir_name}"
        self.flats_dir = f"{self.working_dir}/{self.flats_dir_name}"
        self.darks_dir = f"{self.working_dir}/{self.darks_dir_name}"
        self.lights_dir = f"{self.working_dir}/{self.lights_dir_name}"
        self.process_dir = f"{self.working_dir}/{self.process_dir_name}"
        self.results_dir = f"{self.working_dir}/{self.results_dir_name}"
        self.masters_dir = f"{self.working_dir}/{self.masters_dir_name}"


class Stack(StackConfig):
    '''
    app = Siril()                               # Starts pySiril
    cmd = Wrapper(app)                          # Starts the command wrapper

    help(Siril)                                 # Get help on Siril functions
    help(Wrapper)                               # Get help on all Wrapper functions
    help(Addons)                                # Get help on all Addons functions

    cmd.help()                                  # Lists of all commands
    cmd.help('bgnoise')
    '''

    def __init__(self, working_dir, master_dark_file=None, master_flat_file=None, master_bias_file=None, master_light_file=None, target_ra=None, target_dec=None):
        super().__init__(working_dir=working_dir)
        self.working_dir = working_dir
        self.app = Siril()
        self.siril = Wrapper(self.app)
        self.provision()

        self.master_dark_file = master_dark_file
        self.master_flat_file = master_flat_file
        self.master_bias_file = master_bias_file
        self.master_light_file = master_light_file

        target_name = os.path.basename(
            os.path.normpath(self.working_dir)).replace('_', " ")

        try:
            coords = get_icrs_coordinates(
                name=target_name, parse=False, cache=False)
        except Exception as e:
            print(e)
            coords = None

        c = SkyCoord(
            ra=coords.ra.to(u.deg),
            dec=coords.dec.to(u.deg),
            frame=ICRS,
        ) if coords else None

        self.target_ra = coords.ra.to_string(u.hour) if coords else None
        self.target_dec = coords.dec.to_string(u.hour) if coords else None
        self.constellation = c.get_constellation() if c else None
        print(f"Constellation: {c.get_constellation()}")

    def provision(self):
        Path(self.process_dir).mkdir(parents=True, exist_ok=True)
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        Path(self.masters_dir).mkdir(parents=True, exist_ok=True)

    def start(self):
        self.app.Open()
        self.siril.set16bits()
        self.siril.setext(self.fits_extension)
        self.siril.cd(self.working_dir)

    def get_library_file(self, file_type: str) -> str:
        if file_type == 'bias':
            master_stacked_name = self.bias_stacked_name
        elif file_type == 'dark':
            master_stacked_name = self.dark_stacked_name
        else:
            return ''

        first_light_image_file = f"{self.lights_dir}/{os.listdir(self.lights_dir)[0]}"

        with ExifToolHelper() as exif:
            tags = exif.get_tags(files=first_light_image_file, tags=[
                "EXIF:ISO", "Make", "Model", "ExposureTime"])[0]
            iso = tags.get('EXIF:ISO')
            model = tags.get('EXIF:Model')
            exposure = math.ceil(
                float(tags.get('EXIF:ExposureTime')))
            if file_type == 'dark':
                exposureSec = f"{exposure}s" if file_type == 'dark' else None
                master_file_name = f"{self.master_library_path}/{model} {iso} {exposureSec} {master_stacked_name}.{self.fits_extension}".replace(
                    " ", "_")
            else:
                master_file_name = f"{self.master_library_path}/{model} {iso} {master_stacked_name}.{self.fits_extension}".replace(
                    " ", "_")

            print("")
            print("get_library_file()")
            print(f"master_file_name: {master_file_name}")
            print("")
            print("")
            if os.path.isfile(master_file_name):
                return master_file_name
            else:
                return ""

    def biases(self, save_to_master_library: bool = False, overwrite: bool = False):
        biases_exist = os.path.exists(self.biases_dir) and len(
            os.listdir(self.biases_dir)) != 0

        if biases_exist:
            master_bias_file_exists = os.path.isfile(
                f"{self.masters_dir}{self.bias_stacked_name}.{self.fits_extension}")

            if master_bias_file_exists and not overwrite:
                self.master_bias_file = f"{self.masters_dir}/{self.bias_stacked_name}"
            else:
                self.start()
                self.siril.cd(self.biases_dir_name)
                self.siril.convert(self.bias_conversion_name,
                                   out=self.process_dir,
                                   fitseq=True
                                   )

                self.siril.cd(self.process_dir)
                self.siril.stack(self.bias_conversion_name,
                                 type='rej',
                                 sigma_low=3,
                                 sigma_high=3,
                                 norm='no',
                                 out=self.bias_stacked_name
                                 )

                if save_to_master_library:
                    with ExifToolHelper() as exif:
                        self.siril.load(self.bias_stacked_name)
                        Path(self.master_library_path).mkdir(
                            parents=True, exist_ok=True)
                        self.siril.cd(self.master_library_path)
                        first_image_file = f"{self.biases_dir}/{os.listdir(self.biases_dir)[0]}"
                        tags = exif.get_tags(files=first_image_file, tags=[
                            "EXIF:ISO", "Make", "Model"])[0]
                        iso = tags.get('EXIF:ISO')
                        model = tags.get('EXIF:Model')
                        master_library_name = f"{model} {iso} {self.bias_stacked_name}".replace(
                            " ", "_")
                        self.siril.save(master_library_name)
                        self.siril.cd(self.masters_dir)
                        self.siril.save(self.bias_stacked_name)
                        self.master_bias_file = f"{self.master_library_path}/{self.bias_stacked_name}"
                else:
                    self.master_bias_file = f"{self.masters_dir}/{self.bias_stacked_name}"
                    self.siril.cd(self.masters_dir)
                    self.siril.save(self.bias_stacked_name)
        else:
            raise ("No bias files found")

    def flats(self, overwrite: bool = False):
        flats_exist = os.path.exists(self.flats_dir) and len(
            os.listdir(self.flats_dir)) != 0

        if flats_exist:
            master_flat_exists = os.path.isfile(
                f"{self.masters_dir}{self.flat_stacked_name}.{self.fits_extension}")

            if master_flat_exists and not overwrite:
                self.master_flat_file = f"{self.masters_dir}/{self.flat_stacked_name}"
            else:
                self.start()
                self.siril.cd(self.flats_dir_name)

                self.siril.convert(self.flat_conversion_name,
                                   out=self.process_dir,
                                   fitseq=True
                                   )

                self.siril.cd(self.process_dir)

                master_bias = self.get_library_file('bias')

                print("")
                print("")
                print(f"master_bias: {master_bias}")
                print("")
                print("")

                self.siril.calibrate(self.flat_conversion_name,
                                     bias=master_bias if master_bias else None,
                                     prefix=self.preprocess_prefix
                                     )

                self.siril.stack(self.flat_conversion_name,
                                 type='rej',
                                 sigma_low=3,
                                 sigma_high=3,
                                 norm='mul',
                                 out=self.flat_stacked_name
                                 )

                self.master_flat_file = f"{self.masters_dir}/{self.flat_stacked_name}"
                self.siril.cd(self.masters_dir)
                self.siril.save(self.flat_stacked_name)

    def darks(self, save_to_master_library: bool = False, overwrite: bool = False):
        darks_exist = os.path.exists(self.darks_dir) and len(
            os.listdir(self.darks_dir)) != 0

        if darks_exist:
            master_dark_exists = os.path.isfile(
                f"{self.masters_dir}/{self.dark_stacked_name}.{self.fits_extension}")

            if master_dark_exists and not overwrite:
                self.master_bias_file = f"{self.masters_dir}/{self.dark_stacked_name}"
            else:
                self.start()
                self.siril.cd(self.darks_dir_name)
                self.siril.convert(self.dark_conversion_name,
                                   out=self.process_dir,
                                   fitseq=True
                                   )

                self.siril.cd(self.process_dir)
                self.siril.stack(self.dark_conversion_name,
                                 type='rej',
                                 sigma_low=3,
                                 sigma_high=3,
                                 norm='no',
                                 out=self.dark_stacked_name
                                 )

                if save_to_master_library:
                    with ExifToolHelper() as exif:
                        self.siril.load(self.dark_stacked_name)
                        Path(self.master_library_path).mkdir(
                            parents=True, exist_ok=True)
                        self.siril.cd(self.master_library_path)
                        first_image_file = f"{self.darks_dir}/{os.listdir(self.darks_dir)[0]}"
                        tags = exif.get_tags(files=first_image_file, tags=[
                            "EXIF:ISO", "Make", "Model", "ExposureTime"])[0]
                        iso = tags.get('EXIF:ISO')
                        model = tags.get('EXIF:Model')
                        exposure = math.ceil(
                            float(tags.get('EXIF:ExposureTime')))
                        # TODO: Perhaps add weather conditions to the name (temp range?)
                        master_library_name = f"{model} {iso} {exposure}s {self.dark_stacked_name}".replace(
                            " ", "_")
                        self.siril.save(master_library_name)
                        self.master_dark_file = f"{self.master_library_path}/{master_library_name}"
                        self.siril.cd(self.masters_dir)
                        self.siril.save(self.dark_stacked_name)
                else:
                    self.master_dark_file = f"{self.masters_dir}/{self.dark_stacked_name}"
                    self.siril.cd(self.masters_dir)
                    self.siril.save(self.dark_stacked_name)

    def lights(self):
        lights_exist = os.path.exists(self.darks_dir) and len(
            os.listdir(self.darks_dir)) != 0

        if lights_exist:
            self.start()
            self.siril.cd(self.lights_dir_name)

            self.siril.convert(self.light_conversion_name,
                               out=self.process_dir,
                               fitseq=True
                               )

            self.siril.cd(self.process_dir)

            master_library_dark = self.get_library_file('dark')

            self.master_dark_file = f"{self.master_dark_file}.{self.fits_extension}" if self.master_dark_file else None
            flat_file = f"{self.master_flat_file}.{self.fits_extension}" if self.master_flat_file else None
            dark_file = self.master_dark_file if self.master_dark_file else master_library_dark

            print('')
            print('')
            print("dark_file", dark_file)
            print("flat_file", flat_file)
            print('')
            print('')

            self.siril.calibrate(self.light_conversion_name,
                                 dark=dark_file,
                                 flat=flat_file,
                                 cfa=True,
                                 equalize_cfa=True,
                                 cc='dark',
                                 sighi=3,
                                 siglo=3,
                                 debayer=True,
                                 prefix=self.preprocess_prefix
                                 )

            self.siril.register(
                f"{self.preprocess_prefix}{self.light_conversion_name}",
                nostarlist=True,
                pass2=True
            )

            self.siril.register(
                f"{self.preprocess_prefix}{self.light_conversion_name}",
                nostarlist=True,
                prefix=self.registered_prefix,
            )

            self.siril.stack(f"{self.registered_prefix}{self.preprocess_prefix}{self.light_conversion_name}",
                             type='rej',
                             sigma_low=3,
                             sigma_high=3,
                             norm='addscale',
                             rejection_type="w",
                             rgb_equal=True,
                             out=self.light_stacked_name
                             )

            self.master_light_file = f"{self.masters_dir}/{self.light_stacked_name}"
            self.siril.cd(self.masters_dir)
            self.siril.save(self.light_stacked_name)

    def solve(self):
        self.start()
        self.siril.cd(self.process_dir)
        self.siril.load(f"{self.light_stacked_name}.{self.fits_extension}")
        self.siril.autostretch()
        self.siril.rmgreen()
        self.siril.savejpg(self.light_stacked_name)

        Path(
            f"{self.results_dir}/{self.light_stacked_name}"
        ).mkdir(parents=True, exist_ok=True)

        solve_cmd = [
            'solve-field', f"{self.process_dir}/{self.light_stacked_name}.jpg",
            '-D', f"{self.results_dir}/{self.light_stacked_name}",
            "--downsample", "2",
            "--overwrite",
            "--scale-low", "2",  # 2.24 arcsec per pixel for Sharpstar and T8I
            "--scale-high", "3",  # 2.24 arcsec per pixel for Sharpstar and T8I
            "-u", "arcsecperpix"
        ]

        # if (self.target_ra):
        #     solve_cmd.extend(["--ra", self.target_ra])

        # if (self.target_dec):
        #     solve_cmd.extend(["--dec", self.target_dec])

        print("")
        print(" ".join(solve_cmd))
        print("")

        subprocess.run(solve_cmd)

    def save_preview(self, rmgreen: bool = True, autostretch: bool = True, pcc: bool = True, starnet: bool = True):
        self.start()
        image = f"{self.light_stacked_name}.{self.fits_extension}"

        self.siril.cd(self.process_dir)
        self.siril.load(image)

        if pcc:
            ra, dec = get_center_coords(
                f"{self.results_dir}/{self.light_stacked_name}/{self.light_stacked_name}.wcs"
            )

            if (not ra or not dec):
                ra = self.target_ra
                dec = self.target_dec

            if ra and dec:
                self.siril.pcc(
                    limitmag=0,
                    center_coords=f"{ra},{dec}",
                    platesolve=False,
                    catalog=f"{self.results_dir}/{self.light_stacked_name}/{self.light_stacked_name}.wcs")

        if rmgreen:
            self.siril.rmgreen()

        if autostretch:
            self.siril.autostretch()

        self.siril.cd(self.results_dir)
        self.siril.save(f"{self.light_stacked_name}-preview")
        self.siril.savejpg(f"{self.light_stacked_name}-preview")

        if starnet:
            self.siril.starnet()
            self.siril.load(
                f"starmask_{self.light_stacked_name}.{self.fits_extension}")
            self.siril.savejpg(f"starmask_{self.light_stacked_name}")
            self.siril.load(
                f"starless_{self.light_stacked_name}.{self.fits_extension}")
            self.siril.savejpg(f"starless_{self.light_stacked_name}")

    def hist(self):
        # MOVE THIS OUT TO ITS OWN CLASS OR FUNCTION?
        img = cv.imread(
            f"{self.results_dir}/{self.light_stacked_name}-preview.jpg")
        assert img is not None, "file could not be read, check with os.path.exists()"
        color = ('b', 'g', 'r')
        for i, col in enumerate(color):
            histr = cv.calcHist([img], [i], None, [256], [0, 256])
            plt.plot(histr, color=col)
            plt.xlim([0, 256])
        plt.savefig(
            f"{self.results_dir}/{self.light_stacked_name}-pcc-hist.jpg")

    def split_rgb(self):
        self.start()
        image = f"{self.light_stacked_name}.{self.fits_extension}"
        self.siril.cd(self.masters_dir)
        self.siril.load(image)
        self.siril.split(f"{self.light_stacked_name}-red",
                         f"{self.light_stacked_name}-green", f"{self.light_stacked_name}-blue")

    def done(self):
        self.app.Close()
        del self.app
