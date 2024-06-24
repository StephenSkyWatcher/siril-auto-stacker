import sys
import os
import argparse
from pysiril.siril import *
from pysiril.wrapper import *
from pysiril.addons import Addons

# import exiftool

from .siril import Stack

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--workdir',
                    required=False,
                    type=str,
                    default=None,
                    dest="workdir",
                    metavar="<working directory>",
                    help="Directory with folders: lights, darks, etc...")

parser.add_argument('-B', '--master-bias',
                    required=False,
                    default=None,
                    type=str,
                    dest="MASTER_BIAS_FILE",
                    metavar="<master bias fits file>",
                    help="Optional master bias file")

parser.add_argument('--hist',
                    required=False,
                    default=None,
                    type=str,
                    dest="hist"
                    )

args = parser.parse_args()


# TODO: move histo.dat and perhaps plot it

if args.workdir is not None:
    print("Starting Stack: " + args.workdir)
    # TODO:
    # 1. Split out functionality from siril.py into separate functions/files
    # 2. Create a class to handle the stack process
    #   a. Compare old version with new version and see what is
    #      missing/different b/c the results are different/worse
    # 3. Add more functionality
    #   a. Better platesolving handling
    #   b. Add Annotation processing
    #   c. Add better error handling
    #   d. Add better logging
    # 4. Make executable from command line
    # 5. Look at companion app for ideas
    # 6. Ensure this program is configurable and documented

    # siril.start(
    #     workdir=args.workdir
    # )

    stack = Stack(working_dir=args.workdir)
    # stack.biases(save_to_master_library=True)
    # stack.darks(save_to_master_library=True)
    # stack.flats(try_master_bias=True)
    stack.lights()
    stack.solve()
    stack.post()
    stack.hist()
    stack.done()

    print(stack.master_bias_file)

# app = Siril()                                 # Starts pySiril
# cmd = Wrapper(app)                            # Starts the command wrapper

# help(Siril)                                 # Get help on Siril functions
# help(Wrapper)                               # Get help on all Wrapper functions
# help(Addons)                                # Get help on all Addons functions

# cmd.help()                                  # Lists of all commands
# cmd.help('bgnoise')

# files = ["/home/stephen/Documents/siril-auto-stack/python/stack/sample/m101.cr2"]
# with exiftool.ExifToolHelper() as et:
#     metadata = et.get_metadata(files)
#     for d in metadata:
#         print(d["EXIF:ISO"])
