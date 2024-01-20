import os
import shutil
from dotenv import load_dotenv, dotenv_values
import time
import click
import datetime
from colorama import Fore,Style

from .platesolve import platesolve
from .stack_flats import stackFlats
from .stack_darks import stackDarks
from .stack_lights import stackLights
from .stack_biases import checkBiases
from .post_remove_green import removeGreenNoise
from .post_preview import post_preview
from .starnet import starnet
from .chromatic_abberation import fix_chromatic_abberation
from .photometric_cc import photometric_color_calibration
from .maintenance import createDir, removeDir

load_dotenv()
config = dotenv_values(".env")

STACKED_LIGHTS_NAME=config.get('STACKED_LIGHTS_NAME')
NO_GREEN_NAME=config.get('NO_GREEN_NAME')
TMP_RGB_PROCESS_DIR=config.get('TMP_RGB_PROCESS_DIR')
PROCESS_DIR=config.get('PROCESS_DIR')
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
STACKED_DIR=config.get('STACKED_DIR')
STACKED_BIASES_NAME=config.get('STACKED_BIASES_NAME')

def stack(wd, iso):
    removeDir(f"{wd}/logs")
    createDir(f"{wd}/logs")
    createDir(f"{wd}/{PROCESS_DIR}")
    createDir(SIRIL_TMP_DIR)

    master_bias_fits=f"/home/astrophotography/stack/lib/masters/bias-{iso}-master.fit"
    
    
    try:
        time_firstStart = time.perf_counter()
        
        #  PRE PROCESSING
        current_bias_fits = checkBiases(wd=wd, master_bias_fits=master_bias_fits)
        stackFlats(wd=wd, bias_fits=current_bias_fits)
        stackDarks(wd=wd)
        stackLights(wd=wd)

        #  POST PROCESSING
        platesolve(wd=wd, file=f"{STACKED_LIGHTS_NAME}.fit")
        starnet(wd=wd, file=f"{STACKED_LIGHTS_NAME}.fit")

        # fix_chromatic_abberation(
        #     wd=wd,
        #     file=f"{STACKED_LIGHTS_NAME}.fit"
        # )
              
        # photometric_color_calibration(
        #     wd=wd,
        #     file=f"{STACKED_LIGHTS_NAME}.fit"
        # )

        # post_preview(
        #     wd=wd,
        #     file=f"{STACKED_LIGHTS_NAME}-pcc.fit",
        #     autostretch=True
        # )

        # removeDir(f"{wd}/{PROCESS_DIR}")
        # removeDir(SIRIL_TMP_DIR)

        minutes, seconds = divmod(time.perf_counter() - time_firstStart, 60)
        print(f"Post Processing Grand Total Time: {minutes}m {seconds}s")
        
    except Exception as e:
        print(e.args)
