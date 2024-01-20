from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script
import os
import shutil
load_dotenv()
config = dotenv_values(".env")
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
PROCESS_DIR=config.get('PROCESS_DIR')
STACKED_DIR=config.get('STACKED_DIR')
CHROMATIC_ABBERATION_TEMPLATE=config.get('CHROMATIC_ABBERATION_TEMPLATE')
CHROMATIC_ABBERATION_LOG=config.get('CHROMATIC_ABBERATION_LOG')
STACKED_LIGHTS_NAME=config.get('STACKED_LIGHTS_NAME')
RGB_FIX_NAME=config.get('RGB_FIX_NAME')
TMP_RGB_PROCESS_DIR=config.get('TMP_RGB_PROCESS_DIR')

def removeDir(d):
    if os.path.exists(d):
        shutil.rmtree(d)

def createDir(p):
    if not os.path.exists(p):
        os.makedirs(p)
        
def fix_chromatic_abberation(wd, file):
    removeDir(f"{wd}/{TMP_RGB_PROCESS_DIR}")
    createDir(f"{wd}/{TMP_RGB_PROCESS_DIR}")
    name=file.split('.fit')[0]
    
    write_script(
        name=CHROMATIC_ABBERATION_TEMPLATE,
        content=f'''requires 1.2.0
cd {STACKED_DIR}
LOAD {file}
cd ../{TMP_RGB_PROCESS_DIR}
split r g b 
CONVERT rgb
REGISTER rgb_.seq -prefix=r_ -2pass
REGISTER rgb_ -prefix=r_
rgbcomp r_rgb_00003 r_rgb_00002 r_rgb_00001 -out=../{STACKED_DIR}/{name}-{RGB_FIX_NAME}
autostretch
SAVEJPG ../{STACKED_DIR}/{name}-{RGB_FIX_NAME}-preview 100
''')

    siril(
        title="FIXING CHROMATIC ABBERATION",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{CHROMATIC_ABBERATION_TEMPLATE}",
        log=f"{wd}/{CHROMATIC_ABBERATION_LOG}"
    )
