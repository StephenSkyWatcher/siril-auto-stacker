from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
STARNET_TEMPLATE=config.get('STARNET_TEMPLATE')
STACKED_DIR=config.get('STACKED_DIR')
STARNET_LOG=config.get('STARNET_LOG')

def starnet(wd, file):
    write_script(
        name=STARNET_TEMPLATE,
        content=f'''requires 1.2.0
cd {STACKED_DIR}
LOAD {file}
STARNET -stretch -upscale
'''
)

    siril(
        title="RUNNING STARNET++",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{STARNET_TEMPLATE}",
        log=f"{wd}/{STARNET_LOG}"
    )



