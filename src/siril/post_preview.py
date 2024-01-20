from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
PREVIEW_TEMPLATE=config.get('PREVIEW_TEMPLATE')
STACKED_DIR=config.get('STACKED_DIR')
POST_PREVIEW_LOG=config.get('POST_AUTOSTRETCH_PREVIEW_LOG')

def post_preview(wd, file, autostretch):
    name=file.split('.fit')[0]
    write_script(
        name=PREVIEW_TEMPLATE,
        content=f'''requires 1.2.0
cd {STACKED_DIR}
LOAD {file}
{"autostretch" if autostretch else ""}
SAVEJPG {name}-preview 100
''')

    siril(
        title="CREATING PREVIEW JPG",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{PREVIEW_TEMPLATE}",
        log=f"{wd}/{POST_PREVIEW_LOG}"
    )
