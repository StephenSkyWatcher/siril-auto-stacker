import os
import os.path

from pathlib import Path
import argparse

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from .logger import Logger as _Logger

"""
Stacks a directory of images to a single FITS image

Usage:
    poetry run python -m src.stack darks.seq -f darks

"""

fits_extension = os.getenv('FITS_EXTENSION', 'fit')
cpu_cores = os.getenv('CPU_CORES', os.cpu_count())
process_dir_name = os.getenv('PROCESS_DIR_NAME', 'process')
stacked_prefix = os.getenv('STACKED_PREFIX', 'stacked_')

Logger = _Logger(__name__)
parser = argparse.ArgumentParser()

parser.add_argument('seq', type=str, help="Sequence file to stack")


parser.add_argument('-f', '--frame',
                    required=True,
                    type=str,
                    dest="frame",
                    const='lights',
                    nargs='?',
                    choices=['lights', 'flats', 'darks', 'biases'],
                    help="Frame type to calibrate: lights, flats, farks or biases")

args = parser.parse_args()

App = Siril()  # type: ignore
siril = Wrapper(App)  # type: ignore


def stack(seq=args.seq, frame=args.frame) -> bool:
    siril.setcpu(cpu_cores)
    siril.set16bits()
    siril.setext(fits_extension)
    siril.cd(str(Path(seq).parent))
    Logger.info(f"Stacking Frames")
    name = str(Path(seq).stem)

    stack_params = {
        "out": f"{stacked_prefix}{name}",
        "type": "rej",
        'sigma_low': "3",
        'sigma_high': "3"
    }
    if (frame == 'biases'):
        stack_params['norm'] = 'no'
        stack_params['rejection_type'] = "w"

    if (frame == 'darks'):
        stack_params['norm'] = 'no'
        stack_params['rejection_type'] = "w"

    if (frame == 'flats'):
        stack_params['norm'] = "mul"
        stack_params['rejection_type'] = "w"

    if (frame == 'lights'):
        stack_params['norm'] = "addscale"
        stack_params['rejection_type'] = "l"
        stack_params['rgb_equal'] = True
        stack_params['filter_fwhm'] = "90%"
        stack_params['filter_round'] = "90%"

    Logger.json("Stacking Parameters", stack_params)

    [stack_result] = siril.stack(seq, **stack_params)

    siril.load(f"{stacked_prefix}{name}")

    if stack_result is not True:
        raise Exception(f"Failed to stack {name} sequence")

    return stack_result


if __name__ == "__main__":
    try:
        App.Open()
        stack()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)
    finally:
        Logger.info("Siril Closed")
        App.Close()
