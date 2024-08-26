import os
import os.path

from pathlib import Path
import argparse

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from .logger import Logger as _Logger

"""
Registers a sequence of images

Usage:
    poetry run python -m src.register pp_lights.seq --maxstars=100

"""

prefix = os.getenv('REGISTERED_PREFIX', 'r_')
fits_extension = os.getenv('FITS_EXTENSION', 'fit')
cpu_cores = os.getenv('CPU_CORES', os.cpu_count())

Logger = _Logger(__name__)
parser = argparse.ArgumentParser()


def ranged_type(value_type, min_value, max_value):
    def range_checker(arg: str):
        try:
            f = value_type(arg)
        except ValueError:
            raise argparse.ArgumentTypeError(f'must be a valid {value_type}')
        if f < min_value or f > max_value:
            raise argparse.ArgumentTypeError(
                f'must be within [{min_value}, {max_value}]')
        return f

    return range_checker


parser.add_argument('seq', type=str, help="Sequence file to register")

parser.add_argument('--maxstars',
                    required=True,
                    type=ranged_type(int, 100, 2000),
                    dest="maxstars",
                    help="Maximum number of stars to find within each frame")

args = parser.parse_args()


App = Siril()  # type: ignore
siril = Wrapper(App)  # type: ignore


def register(
    seq=args.seq,
    maxstars=args.maxstars,
) -> bool:
    siril.setcpu(cpu_cores)
    siril.set16bits()
    siril.setext(fits_extension)
    siril.cd(str(Path(seq).parent))

    Logger.info(f"Registering light Frames")
    name = Path(seq).stem

    GREEN_CHANNEL = 1

    # [-2pass] [-noout] [-drizzle] [-prefix=] [-minpairs=] [-transf=] [-layer=] [-maxstars=] [-nostarlist] [-interp=] [-selected]
    registration_params = {
        "nostarlist": True,
        "prefix": prefix,
        "layer": GREEN_CHANNEL,
        "maxstars": maxstars
    }

    Logger.json("Registration Params", registration_params)

    [pass2_result] = siril.register(name, **registration_params, pass2=True)

    if pass2_result is not True:
        raise Exception(f"Failed to register {name} Frames (2-pass)")

    [registration_result] = siril.register(
        name, **registration_params, drizzle=True)

    if registration_result is not True:
        raise Exception(f"Failed to register {name} Frames with drizzle")

    Logger.info(f"Registered light Frames")

    return True


if __name__ == "__main__":
    try:
        App.Open()
        register()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)
    finally:
        Logger.info("Siril Closed")
        App.Close()
