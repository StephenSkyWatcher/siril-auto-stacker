from dotenv import load_dotenv, dotenv_values
import os
import time
import click
from colorama import Fore,Style
from astropy.io import fits
from astropy.wcs import WCS
from astropy.utils.data import get_pkg_data_filename
from astropy import units as u
from astropy.coordinates import SkyCoord

from .platesolve import platesolve
from .stack_flats import stackFlats
from .stack_darks import stackDarks
from .stack_lights import stackLights
from .stack_biases import checkBiases
from .starnet import starnet
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
FINAL_DETAIL_LOG=config.get('FINAL_DETAIL_LOG')

def logCenterCoordinates(wd):
    try:
        os.remove(f"{wd}/{FINAL_DETAIL_LOG}")
    except:
        print()

    f = fits.open(f"{wd}/{STACKED_DIR}/{STACKED_LIGHTS_NAME}.fits")
    c = SkyCoord(ra=f[0].header['RA']*u.degree, dec=f[0].header['DEC']*u.degree)
    print(f"{Fore.MAGENTA}HMS/DMS: {Fore.RESET}{c.to_string('hmsdms')}")

    # TODO: Remove trailing comma, better yet, find a cleaner way to do this
    with open(f"{wd}/{FINAL_DETAIL_LOG}", 'ab') as file:
        file.write('{'.encode())
        for count, hdu in enumerate(repr(f[0].header).split('\n')):
            if ('=' in hdu.split('/')[0]):
                try:
                    if (' ' not in hdu.split('/')[0].split('=')[0].strip()):
                        file.write((\
                            '"' + hdu.split('/')[0].split('=')[0].strip() + \
                            '": "' + hdu.split('/')[0].split('=')[1].strip().replace("'", '') + \
                            '",\n'\
                        ).encode())
                except:
                    continue
        file.write('}'.encode())

def stack(wd, iso):    
    shouldPlateSolve=click.confirm(f"{Fore.CYAN}Do you wish to plate solve?{Fore.RESET}", default=True)
    shouldStarnet=click.confirm(f"{Fore.CYAN}Do you wish to run Starnet++?{Fore.RESET}", default=True)
    removeProcess=click.confirm(f"{Fore.CYAN}Do you wish to remove process files as the end?{Fore.RESET}", default=True)

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
        if (shouldPlateSolve):
            platesolve(wd=wd, file=f"{STACKED_LIGHTS_NAME}.fits")

        if (shouldStarnet):
            starnet(wd=wd, file=f"{STACKED_LIGHTS_NAME}.fits")

        # photometric_color_calibration(
        #     wd=wd,
        #     file=f"{STACKED_LIGHTS_NAME}.fits"
        # )

        if (removeProcess):
            removeDir(f"{wd}/{PROCESS_DIR}")
        removeDir(SIRIL_TMP_DIR)

        minutes, seconds = divmod(time.perf_counter() - time_firstStart, 60)
        print(f"Post Processing Grand Total Time: {minutes}m {seconds}s")
        
        logCenterCoordinates(wd)
    except Exception as e:
        print(e.args)

#TODO: consider FWHM < 4 and Eccentricity < 0.5