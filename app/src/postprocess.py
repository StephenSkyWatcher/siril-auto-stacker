import os
import os.path
import subprocess

from pathlib import Path
import argparse

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from astropy import units as u
from astropy.coordinates import (ICRS, SkyCoord, get_icrs_coordinates)

from .logger import Logger as _Logger

"""
Stacks a directory of images to a single FITS image

Usage:
    poetry run python -m src.stack darks.seq -f darks

"""

fits_extension = os.getenv('FITS_EXTENSION', 'fit')
cpu_cores = os.getenv('CPU_CORES', os.cpu_count())
process_dir_name = os.getenv('PROCESS_DIR_NAME', 'process')

Logger = _Logger(__name__)
parser = argparse.ArgumentParser()

parser.add_argument('file', type=str, help="FITS file to process")

parser.add_argument('-t', '--target',
                    required=False,
                    type=str,
                    dest="target",
                    help="Target name")

args = parser.parse_args()

App = Siril()  # type: ignore
siril = Wrapper(App)  # type: ignore


target_ra_hms = None
target_dec_dms = None
target_ra = None
target_dec = None
constellation = None


def try_target_data():
    global target_ra_hms, target_dec_dms, target_ra, target_dec, constellation

    # TODO: Consider looking at details.json
    # TODO: Make this more resiliant

    try:
        coords = get_icrs_coordinates(
            name=args.target, parse=False, cache=False)
    except Exception as e:
        print(e)
        coords = None

    c = SkyCoord(
        ra=coords.ra.to(u.deg),
        dec=coords.dec.to(u.deg),
        frame=ICRS,
    ) if coords else None

    target_ra_hms = coords.ra.to_string(u.hour) if coords else None
    target_dec_dms = coords.dec.to_string(u.hour) if coords else None

    target_ra = coords.ra.value if coords else None
    target_dec = coords.dec.value if coords else None

    constellation = c.get_constellation() if c else None

    Logger.info(f"Target: {args.target}")
    Logger.info(f"Coords: {target_ra_hms} {target_dec_dms}")
    Logger.info(f"Coords: {target_ra} {target_dec}")
    Logger.info(f"Constellation: {constellation}")


def _solve(ra,
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

    Logger.info(f"Plate Solving")

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

    Logger.json("Plate Solve Params", platesolve_params)

    [solve_success] = siril.platesolve(**platesolve_params)

    if solve_success is not True:
        Logger.warning(f"Plate Solve Error: {solve_success}")
    else:
        Logger.info(f"Plate Solving Completed")


def remove_gradient(file, gpu=False):
    Logger.info(f"Running GraXpert Background Extraction")
    gradient_cmd = [
        "graxpert",
        file,
        "-cli",
        "-correction", "Subtraction",
        "-smoothing", "0.2",
        "-bg",
        "-gpu", "true" if gpu else "false",
        "--command", "background-extraction"
    ]
    subprocess.run(gradient_cmd)


def process_stars(starmask):
    siril.load(starmask)
    siril.save(f"{starmask}.bak")

    # ASINH Stretch
    Logger.info(f"ASINH Stretch: 0 // 0.2 on Stars")
    [completed] = siril.asinh(
        1, human=True, offset=0.2)
    if completed is not True:
        raise Exception("ASINH Stretch on Stars Failed")
    else:
        siril.save(f"{starmask}")

    Logger.info(f"Denoising Stars")
    [completed] = siril.denoise(mod=1, nocosmetic=False, da3d=False)
    if completed is not True:
        raise Exception("Denoising Stars Failed")
    else:
        siril.save(starmask)


def process_starless(file):
    starless = f"starless_{Path(file).stem}-processed"
    siril.save(f"{starless}.bak")

    remove_gradient(f"{os.path.dirname(file)}/starless_{Path(file).name}")

    # To be generated from running GraXpert
    starless_graxpert_path = f"{os.path.dirname(file)}/starless_{Path(file).stem}-processed_GraXpert.fits"

    siril.load(starless_graxpert_path)
    siril.save(f"{starless}-graxpert")

    # os.remove("_GraXpert.fits")


def star_recomposition(starless, starmask, name):
    Logger.info(
        f"Combining Starless and Starmask with PixelMath: Starless: {starless}.fit   Stars: {starmask}.fit")

    siril.pm(
        expression=f"${starless}.fit$ * 0.5 + ${starmask}.fit$ * 0.5",
        rescale=True,
        low=0.0,
        high=0.9
    )

    siril.save(f"{name}-recomposed")


def postprocess(file=args.file, target=args.target) -> bool:
    siril.setcpu(cpu_cores)
    siril.set16bits()
    siril.setext(fits_extension)
    siril.cd(str(Path(file).parent))
    Logger.info(f"Starting Post-Processing")
    name = str(Path(file).stem)

    # Save backup
    siril.load(file)
    # siril.save(f"{Path(file).stem}.bak")
    # siril.load(file)

    # siril.rmgreen()

    # if target:
    #     try_target_data()

    # if target_dec and target_ra:
    #     _solve(
    #         ra=target_ra,
    #         dec=target_dec,
    #         localasnet=False,
    #         force=True,
    #         downscale=True,
    #         noflip=False,
    #         catalog=None,
    #     )

    #     siril.pcc(
    #         center_coords=f"{target_ra},{target_dec}",
    #         platesolve=False,
    #     )

    # siril.save(f"{name}-processed")
    # siril.load(f"{name}-processed")
    siril.starnet(stretch=True)

    starmask = f"starmask_{name}-processed"
    starless = f"starless_{name}-processed"

    process_stars(file)
    process_starless(file)

    star_recomposition(starless, starmask, name)


if __name__ == "__main__":
    try:
        App.Open()
        postprocess()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)
    finally:
        Logger.info("Siril Closed")
        App.Close()
