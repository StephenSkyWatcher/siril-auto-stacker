import os
from exiftool import ExifToolHelper  # type: ignore

from ..logger import Logger as _Logger
from .frame import Frame

Logger = _Logger(__name__)


def get_camera_exif(light: Frame, night: str = None) -> tuple:
    try:
        Logger.info("Getting camera ISO and Model")
        first_light_image_file = f"{light.dir}/{night}/{os.listdir(light.dir)[0]}" if night else f"{light.dir}/{os.listdir(light.dir)[0]}"

        Logger.info(f"first_light_image_file: {first_light_image_file}")
        with ExifToolHelper() as exif:
            tags = exif.get_tags(files=first_light_image_file, tags=[
                "EXIF:ISO", "Make", "Model"])[0]
            iso = tags.get('EXIF:ISO')
            model = tags.get('EXIF:Model').replace(' ', "_")

        Logger.info(f"ISO: {iso}, Model: {model}")
        return (iso, model)
    except Exception as e:
        Logger.error('get_camera_exif failed')
        raise e


def get_library_file(type: Frame, light=Frame, night: str = None) -> str:
    try:
        if type.name != os.environ['BIASES_NAME']:
            raise Exception("Only Master Biases are supported for now")

        (iso, model) = get_camera_exif(light, night=night)

        master_library_filepath = "/".join([
            # /master-library
            f"{os.environ['BIAS_LIBRARY']}",
            # /Canon_EOS_Rebel_T8i
            model,
            # /biases
            os.environ['BIASES_DIR_NAME'],
            # /Canon_EOS_Rebel_T8i_800_stacked_bias
            f"{model}_{iso}_{os.environ['BIASES_STACKED_PREFIX']}{os.environ['BIASES_NAME']}"
            # .fit
        ]) + f".{os.environ['FITS_EXTENSION']}"

        Logger.info(f"master_file_name: {master_library_filepath}")

        if os.path.isfile(master_library_filepath):
            return master_library_filepath
        else:
            return ""

    except Exception as e:
        Logger.error('get_library_file failed')
        raise e
