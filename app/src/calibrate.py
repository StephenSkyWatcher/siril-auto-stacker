import os
import os.path

from pathlib import Path
import argparse

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from .logger import Logger as _Logger

"""
Calibrates a sequence of images

Usage:
    poetry run python -m src.calibrate flats.fit -F flats -fitseq --bias=master_bias.fit

"""

prefix = os.getenv('PREPROCESS_PREFIX', 'pp_')
fits_extension = os.getenv('FITS_EXTENSION', 'fit')
cpu_cores = os.getenv('CPU_CORES', os.cpu_count())

Logger = _Logger(__name__)
parser = argparse.ArgumentParser()

parser.add_argument('seq', type=str, help="Sequence file to calibrate")

parser.add_argument('-f', '--frame',
                    required=True,
                    type=str,
                    dest="frame",
                    const='lights',
                    nargs='?',
                    choices=['lights', 'flats'],
                    help="Frame type to calibrate: lights, flats")

parser.add_argument('-B', '--bias',
                    required=False,
                    type=str,
                    default=None,
                    dest="master_bias",
                    help="Master bias file to use for calibration")

parser.add_argument('-D', '--dark',
                    required=False,
                    type=str,
                    default=None,
                    dest="master_dark",
                    help="Master dark file to use for calibration")

parser.add_argument('-F', '--flat',
                    required=False,
                    type=str,
                    default=None,
                    dest="master_flat",
                    help="Master flat file to use for calibration")

parser.add_argument('-fitseq',
                    required=False,
                    action='store_const',
                    const=True,
                    default=False,
                    dest="fitseq",
                    help="Should use a FITS sequence?")

args = parser.parse_args()


App = Siril()  # type: ignore
siril = Wrapper(App)  # type: ignore

if args.frame == 'flats' and args.master_bias is None:
    Logger.warn("Not using Master Bias for Flats Calibration")


def calibrate(
    seq=args.seq,
    frame=args.frame,
    fitseq=args.fitseq,
    master_bias=args.master_bias,
    master_dark=args.master_dark,
    master_flat=args.master_flat,
) -> bool:
    siril.setcpu(cpu_cores)
    siril.set16bits()
    siril.setext(fits_extension)
    siril.cd(str(Path(seq).parent))

    Logger.info(f"Converting Frames")
    name = Path(seq).stem

    calibrate_params = {
        "cfa": True,
        "equalize_cfa": True,
        "all": True,
        "prefix": prefix,
        "sighi": 3,
        "siglo": 3,
        "fitseq": fitseq
    }

    if frame == 'lights':
        calibrate_params["debayer"] = True

        if master_dark is not None:
            calibrate_params["dark"] = master_dark
            calibrate_params["cc"] = 'dark'

        if master_flat is not None:
            calibrate_params["flat"] = master_flat

    if frame == "flats" and master_bias is not None:
        calibrate_params["bias"] = master_bias

    Logger.json("Calibration Parameters", calibrate_params)

    [calibrate_result] = siril.calibrate(
        name, **calibrate_params)

    if calibrate_result is not True:
        raise Exception(f"Failed to calibrate {name} Frames")

    return calibrate_result


if __name__ == "__main__":
    try:
        App.Open()
        calibrate()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)
    finally:
        Logger.info("Siril Closed")
        App.Close()
