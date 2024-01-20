from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
PHOTOMETRIC_CC_TEMPLATE=config.get('PHOTOMETRIC_CC_TEMPLATE')
STACKED_DIR=config.get('STACKED_DIR')
PHOTOMETRIC_CC_LOG=config.get('PHOTOMETRIC_CC_LOG')

def photometric_color_calibration(wd, file):
    name=file.split('.fit')[0]
    write_script(
        name=PHOTOMETRIC_CC_TEMPLATE,
        content=f'''requires 1.2.0
cd {STACKED_DIR}
LOAD {file}
PCC
SAVE {name}-pcc
LOAD {name}-pcc
DENOISE -mod=0.5 -nocosmetic
SAVE {name}-pcc-denoise
''')

    siril(
        title="PHOTOMETRIC COLOR CALIBRATION",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{PHOTOMETRIC_CC_TEMPLATE}",
        log=f"{wd}/{PHOTOMETRIC_CC_LOG}"
    )