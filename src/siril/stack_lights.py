from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")

CPU_THREADS=config.get('CPU_THREADS')
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
LIGHTS_TEMPLATE=config.get('LIGHTS_TEMPLATE')
LIGHTS_LOG=config.get('LIGHTS_LOG')
PROCESS_DIR=config.get('PROCESS_DIR')
STACKED_DIR=config.get('STACKED_DIR')
STACKED_LIGHTS_NAME=config.get('STACKED_LIGHTS_NAME')
STACKED_DARKS_NAME=config.get('STACKED_DARKS_NAME')
STACKED_FLATS_NAME=config.get('STACKED_FLATS_NAME')

def stackLights(wd):
    write_script(
        name=LIGHTS_TEMPLATE,
        content=f'''requires 1.2.0
SETCPU {CPU_THREADS}
cd lights
# CONVERT lights -out=../{PROCESS_DIR}
# cd ../{PROCESS_DIR}
# CALIBRATE lights_.seq -dark=../{STACKED_DIR}/{STACKED_DARKS_NAME}.fit -flat=../{STACKED_DIR}/{STACKED_FLATS_NAME}.fit -cfa -equalize_cfa -cc=dark 3 3 -debayer -prefix=pp_
# REGISTER pp_lights_.seq -prefix=r_ -2pass
# REGISTER pp_lights_.seq -prefix=r_
# STACK r_pp_lights_.seq rej l 3 3 -norm=addscale -output_norm -rgb_equal -out=../{STACKED_DIR}/{STACKED_LIGHTS_NAME}
cd ../{STACKED_DIR}
LOAD {STACKED_LIGHTS_NAME}
RMGREEN
SAVE {STACKED_LIGHTS_NAME}
LOAD {STACKED_LIGHTS_NAME}
AUTOSTRETCH
SAVEJPG {STACKED_LIGHTS_NAME}-preview 100
'''
)

    siril(
        title="STACKING LIGHT FRAMES",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{LIGHTS_TEMPLATE}",
        log=f"{wd}/{LIGHTS_LOG}"
    )

