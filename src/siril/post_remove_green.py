from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")

SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
STACKED_DIR=config.get('STACKED_DIR')
REMOVE_GREEN_TEMPLATE=config.get('REMOVE_GREEN_TEMPLATE')
POST_REMOVE_GREEN_LOG=config.get('POST_REMOVE_GREEN_LOG')
NO_GREEN_NAME=config.get('NO_GREEN_NAME')

def removeGreenNoise(wd, file):
    write_script(
        name=REMOVE_GREEN_TEMPLATE,
        content=f'''requires 1.2.0
cd {STACKED_DIR}
LOAD {file}
RMGREEN 
SAVE {NO_GREEN_NAME}-{file}
'''
)

    siril(
        title="PLATE SOLVING",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{REMOVE_GREEN_TEMPLATE}",
        log=f"{wd}/{POST_REMOVE_GREEN_LOG}"
    )
