import os
from pathlib import Path

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

import argparse
from .siril import SirilWrapper, Frame, PostProcess, Session
from .logger import Logger as _Logger

with open(os.environ['INFO_LOG_FILE'], 'r+') as f:
    f.truncate(0)

with open(os.environ['ERROR_LOG_FILE'], 'r+') as f:
    f.truncate(0)

_Siril = Siril()  # type: ignore
Logger = _Logger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--workdir',
                    required=False,
                    type=str,
                    default=None,
                    dest="workdir",
                    metavar="<working directory>",
                    help="Directory with folders: lights, darks, etc...")

args = parser.parse_args()

if args.workdir is None:
    Logger.error("No working directory specified")
    exit(1)

# ===========================================

DELETE_WORK_AFTER_PROCESSING = False

biases = Frame(
    name=os.environ['BIASES_NAME'],
    dir=os.environ['BIASES_DIR_NAME'],
    process_dir=os.environ['PROCESS_DIR_NAME'],
    stacked_prefix=os.environ['BIASES_STACKED_PREFIX'],
)

darks = Frame(
    name=os.environ['DARKS_NAME'],
    dir=os.environ['DARKS_DIR_NAME'],
    process_dir=os.environ['PROCESS_DIR_NAME'],
    stacked_prefix=os.environ['DARKS_STACKED_PREFIX'],
)

flats = Frame(
    name=os.environ['FLATS_NAME'],
    dir=os.environ['FLATS_DIR_NAME'],
    process_dir=os.environ['PROCESS_DIR_NAME'],
    stacked_prefix=os.environ['FLATS_STACKED_PREFIX'],
)

lights = Frame(
    name=os.environ['LIGHTS_NAME'],
    dir=os.environ['LIGHTS_DIR_NAME'],
    process_dir=os.environ['PROCESS_DIR_NAME'],
    stacked_prefix=os.environ['LIGHTS_STACKED_PREFIX'],
)

session = Session(
    working_dir=args.workdir,
    biases=biases,
    darks=darks,
    flats=flats,
    lights=lights,
    multiple=True
)

siril = SirilWrapper(
    sirilApp=_Siril,  # type: ignore
    sirilWrapper=Wrapper(_Siril),  # type: ignore
    remove_work=DELETE_WORK_AFTER_PROCESSING,
    session=session
)

post = PostProcess(siril, lights)

try:
    """
    TODO: Add support for stacking multiple nights
        - For each night
            - Convert & Calibrate each night separately
            - (maybe?) Convert pp_lights1, pp_lights2... into sequence files
        - Final
            - Register & Stack all of them together
    TODO: Add support for stacking multiple exposures of same target
    """

    siril.start()

    def post_process():
        post\
            .load(siril.get_stacked_file(lights))\
            .nebula(
                stretch=True,
                ra=siril.target_ra,  # decimal degrees
                dec=siril.target_dec,  # decimal degrees
                remove_work=True,
                denoise=False,
                star_stretch=True,
                extra_star_denoise=False,
            )

    siril.preprocess(darks, delete_raws=True)
    siril.preprocess(flats, delete_raws=True)
    siril.preprocess(lights, delete_raws=True)

    # siril.stack(lights, rmgreen=False)

    """
    post\
        .load(siril.get_stacked_file(lights))\
        .autostretch()\
        .solve(
            ra=siril.target_ra,  # decimal degrees
            dec=siril.target_dec,  # decimal degrees
            force=True,
        )\
        .jsonmetadata()\
        .preview('test-preview2', type='tif8')
    """

    siril.stop()
    Logger.info("[COMPLETED] Success!")
except Exception as e:
    Logger.error(e)
    siril.stop()
    Logger.error("[COMPLETED] Error!")
    exit(1)


# post.solve_test(stacked_lights)
# post.solve(
#     stacked_lights,
#     # 2.24 arcsec per pixel for Sharpstar and T8I
#     stretch=False,
#     ra="10.919",
#     dec="41.382",
#     scale_low=2.24,
#     scale_high=2.24,
#     unit='arcsecperpix'
# )
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
