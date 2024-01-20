import os
import shutil
from dotenv import load_dotenv, dotenv_values
import time
import datetime
from .platesolve import platesolve
from .stack_flats import stackFlats
from .stack_darks import stackDarks
from .stack_lights import stackLights
from .post_remove_green import removeGreenNoise
from .post_preview import post_preview
from .starnet import starnet
from .chromatic_abberation import fix_chromatic_abberation
from .photometric_cc import photometric_color_calibration

load_dotenv()
config = dotenv_values(".env")

STACKED_LIGHTS_NAME=config.get('STACKED_LIGHTS_NAME')
NO_GREEN_NAME=config.get('NO_GREEN_NAME')
TMP_RGB_PROCESS_DIR=config.get('TMP_RGB_PROCESS_DIR')
PROCESS_DIR=config.get('PROCESS_DIR')
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')

# TODO SHARE THIS
def removeDir(d):
    if os.path.exists(d):
        shutil.rmtree(d)
    
# TODO SHARE THIS
def createDir(p):
    if not os.path.exists(p):
        os.makedirs(p)

def stack(wd, iso):
    removeDir(f"{wd}/logs")
    createDir(f"{wd}/logs")
    createDir(f"{wd}/{PROCESS_DIR}")
    createDir(SIRIL_TMP_DIR)

    master_bias_fits=f"/home/astrophotography/stack/lib/masters/bias-{iso}-master.fit"

    # TODO: Check if biases/ exists and if so, create new bias master?
    
    try:
        time_firstStart = time.perf_counter()

        # time_start = time.perf_counter()
        # stackFlats(wd=wd, master_bias_fits=master_bias_fits)
        # print(f"Stacking Flats Total Time: {round(time.perf_counter() - time_start, 2)}")

        # time_start = time.perf_counter()
        # stackDarks(wd=wd)
        # print(f"Stacking Darks Total Time: {round(time.perf_counter() - time_start, 2)}")

        time_start = time.perf_counter()
        stackLights(wd=wd)
        print(f"Stacking Lights Total Time: {round(time.perf_counter() - time_start, 2)}")
        
        # time_start = time.perf_counter()
        # platesolve(wd=wd, file=f"{STACKED_LIGHTS_NAME}.fit")
        # print(f"Plate Solve Total Time: {round(time.perf_counter() - time_start, 2)}")
        
        # time_start = time.perf_counter()
        # starnet(wd=wd, file=f"{STACKED_LIGHTS_NAME}.fit")
        # print(f"Starnet++ Total Time: {round(time.perf_counter() - time_start, 2)}")

        # post_preview(
        #     wd=wd,
        #     file=f"starless_{STACKED_LIGHTS_NAME}.fit",
        #     autostretch=True
        # )

        # post_preview(
        #     wd=wd,
        #     file=f"starmask_{STACKED_LIGHTS_NAME}.fit",
        #     autostretch=False
        # )
        

        time_start = time.perf_counter()
        fix_chromatic_abberation(
            wd=wd,
            file=f"{STACKED_LIGHTS_NAME}.fit"
        )
        print(f"Chromatic Abberation Total Time: {round(time.perf_counter() - time_start, 2)}")

        time_start = time.perf_counter()
        photometric_color_calibration(
            wd=wd,
            file=f"{STACKED_LIGHTS_NAME}.fit"
        )
        print(f"Photometric Color Calibration Total Time: {round(time.perf_counter() - time_start, 2)}")

        post_preview(
            wd=wd,
            file=f"{STACKED_LIGHTS_NAME}-pcc.fit",
            autostretch=True
        )

        removeDir(f"{wd}/{PROCESS_DIR}")
        removeDir(SIRIL_TMP_DIR)

        minutes, seconds = divmod(time.perf_counter() - time_firstStart, 60)
        print(f"Post Processing Grand Total Time: {minutes}m {seconds}s")
        

    except Exception as e:
        print(e.args)
