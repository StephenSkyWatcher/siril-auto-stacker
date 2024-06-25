import argparse
from .siril import Stack

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
    stack = Stack(working_dir=args.workdir)
    stack.biases(save_to_master_library=True)
    stack.darks(save_to_master_library=True)
    stack.flats(try_master_bias=True)
    stack.lights(try_master_darks=True)
    stack.solve()
    stack.save_preview()
    # # stack.hist()
    # stack.split_rgb()
    stack.done()

    print(stack.master_bias_file)
