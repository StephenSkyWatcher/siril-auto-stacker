import argparse
from .siril import SirilWrapper, Biases, Darks
from .logger import Logger as _Logger

Logger = _Logger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--workdir',
                    required=False,
                    type=str,
                    default=None,
                    dest="workdir",
                    metavar="<working directory>",
                    help="Directory with folders: lights, darks, etc...")

# parser.add_argument('-B', '--master-bias',
#                     required=False,
#                     default=None,
#                     type=str,
#                     dest="MASTER_BIAS_FILE",
#                     metavar="<master bias fits file>",
#                     help="Optional master bias file")

args = parser.parse_args()

if args.workdir is not None:
    Siril = SirilWrapper(
        working_dir=args.workdir,
        biases_library="/home/stephen/Pictures/andromeda_galaxy/biases/library"
    )

    Siril.start()
    biases = Biases(Siril)
    darks = Darks(Siril)

    # BIASES
    biases.convert()
    biases.stack()
    biases.save_to_master_library()
    master_bias_file = biases.get_master_library_file()
    stacked_bias = biases.get_stacked_file()
    Logger.info(f"Master Bias File: {master_bias_file}")
    Logger.info(f"Stacked Bias File: {stacked_bias}")

    # DARKS
    darks.convert()
    darks.stack()
    stacked_dark = darks.get_stacked_file()
    Logger.info(f"Stacked Dark File: {stacked_dark}")

    # FLATS

    # LIGHTS

    Siril.stop()

    # stack = Stack(working_dir=args.workdir)
    # stack.biases(save_to_master_library=True, overwrite=True)
    # stack.darks(save_to_master_library=True, overwrite=True)
    # stack.flats(overwrite=True)
    # stack.lights()
    # stack.get_library_file('bias')
    # stack.get_library_file('bias')
    # stack.solve()
    # stack.save_preview()
    # stack.hist()
    # stack.split_rgb()
    # stack.done()

    # print(stack.master_bias_file)
