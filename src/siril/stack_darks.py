import time
from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")

CPU_THREADS=config.get('CPU_THREADS')
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
DARKS_TEMPLATE=config.get('DARKS_TEMPLATE')
DARKS_LOG=config.get('DARKS_LOG')
PROCESS_DIR=config.get('PROCESS_DIR')
STACKED_DIR=config.get('STACKED_DIR')
STACKED_DARKS_NAME=config.get('STACKED_DARKS_NAME')

def stackDarks(wd):
    time_start = time.perf_counter()

    write_script(
        name=DARKS_TEMPLATE,
        content=f'''requires 1.2.0
SETCPU {CPU_THREADS}
cd darks
convert darks -out=../{PROCESS_DIR}

cd ../{PROCESS_DIR}
stack darks_.seq rej w 3 3 -nonorm -out=../{STACKED_DIR}/{STACKED_DARKS_NAME}
'''
)

    siril(
        title="STACKING DARK FRAMES",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{DARKS_TEMPLATE}",
        log=f"{wd}/{DARKS_LOG}"
    )
    print(f"Stacking Darks Total Time: {round(time.perf_counter() - time_start, 2)}")
