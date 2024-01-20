from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")

CPU_THREADS=config.get('CPU_THREADS')
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
FLATS_TEMPLATE=config.get('FLATS_TEMPLATE')
FLATS_LOG=config.get('FLATS_LOG')
PROCESS_DIR=config.get('PROCESS_DIR')
STACKED_DIR=config.get('STACKED_DIR')
STACKED_FLATS_NAME=config.get('STACKED_FLATS_NAME')

def stackFlats(wd, master_bias_fits):
    write_script(
        name=FLATS_TEMPLATE,
        content=f'''\
requires 1.2.0
SETCPU {CPU_THREADS}
cd flats
CONVERT flats -out=../{PROCESS_DIR}

cd ../{PROCESS_DIR}
CALIBRATE flats_.seq -bias={master_bias_fits} -cfa -equalize_cfa -prefix=pp_

STACK pp_flats_.seq rej w 3 3 -norm=mul -out=../{STACKED_DIR}/{STACKED_FLATS_NAME}
'''
)

    siril(
        title="STACKING FLAT FRAMES",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{FLATS_TEMPLATE}",
        log=f"{wd}/{FLATS_LOG}"
    )
