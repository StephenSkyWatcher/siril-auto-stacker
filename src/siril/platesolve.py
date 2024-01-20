from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")

SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
PLATESOLVE_TEMPLATE=config.get('PLATESOLVE_TEMPLATE')
STACKED_DIR=config.get('STACKED_DIR')
PLATESOLVE_LOG=config.get('PLATESOLVE_LOG')
STACKED_LIGHTS_NAME=config.get('STACKED_LIGHTS_NAME')

def platesolve(wd, file):
    write_script(
        name=PLATESOLVE_TEMPLATE,
        content=f'''requires 1.2.0
cd {STACKED_DIR}
LOAD {file}
PLATESOLVE -localasnet 
SAVE {file}
'''
)

    siril(
        title="PLATE SOLVING",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{PLATESOLVE_TEMPLATE}",
        log=f"{wd}/{PLATESOLVE_LOG}"
    )
