import os
import os.path

from pathlib import Path
import argparse

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from .logger import Logger as _Logger

"""
Converts a directory of images to FITS format

Usage:
    poetry run python -m src.convert /home/stephen/Documents/siril-auto-stack/sample/pleiades-sm/lights -fitseq

"""

fits_extension = os.getenv('FITS_EXTENSION', 'fit')
cpu_cores = os.getenv('CPU_CORES', os.cpu_count())
process_dir_name = os.getenv('PROCESS_DIR_NAME', 'process')

Logger = _Logger(__name__)
parser = argparse.ArgumentParser()

parser.add_argument(
    'src', type=str, help="Source directory for images to convert")

parser.add_argument('-o', '--out',
                    required=False,
                    type=str,
                    default=None,
                    dest="out",
                    help="Desination for converted files")

parser.add_argument('-fitseq',
                    required=False,
                    action='store_const',
                    const=True,
                    default=False,
                    dest="fitseq",
                    help="Should use a FITS sequence?")

parser.add_argument('-debayer',
                    required=False,
                    action='store_const',
                    const=True,
                    default=False,
                    dest="debayer",
                    help="Should the images be debayered?")

args = parser.parse_args()

if args.out is None:
    Logger.warning(
        "Dest directory not specified with -o or --out - using src directory")
    args.out = f"{args.src}/{process_dir_name}"


App = Siril()  # type: ignore
siril = Wrapper(App)  # type: ignore


def convert(src=args.src, out=args.out, fitseq=args.fitseq, debayer=args.debayer) -> bool:
    siril.setcpu(cpu_cores)
    siril.set16bits()
    siril.setext(fits_extension)
    siril.cd(src)
    Logger.info(f"Converting Frames")
    name = Path(src).stem

    conversion_params = {
        "out": out,
        "fitseq": fitseq,
        "debayer": debayer
    }

    Logger.json("Conversion Params", conversion_params)

    [conversion_result] = siril.convert(name, **conversion_params)

    if conversion_result is not True:
        raise Exception(f"Failed to convert {name} Frames")

    return conversion_result


if __name__ == "__main__":
    try:
        App.Open()
        convert()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)
    finally:
        Logger.info("Siril Closed")
        App.Close()
