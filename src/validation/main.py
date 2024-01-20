from exiftool import ExifToolHelper
import argparse
import os
from colorama import Fore
import pprint
from dotenv import load_dotenv, dotenv_values

from src.exif import get_luminance_value, get_required_exif_tags, validate_sibling_frame_exif_tags

load_dotenv()
config = dotenv_values(".env")

pp = pprint.PrettyPrinter(indent=4).pprint

# Move/use env/config file
AMBIENT_TEMP_VARIANCE=int(config.get('AMBIENT_TEMP_VARIANCE'))
AMBIENT_TEMP_VARIANCE_WARN=int(config.get('AMBIENT_TEMP_VARIANCE_WARN'))
DARK_LUMINANCE_VARIANCE=int(config.get('DARK_LUMINANCE_VARIANCE'))
DARK_LUMINANCE_VARIANCE_WARN=int(config.get('DARK_LUMINANCE_VARIANCE_WARN'))
BIAS_LUMINANCE_VARIANCE=int(config.get('BIAS_LUMINANCE_VARIANCE'))
BIAS_LUMINANCE_VARIANCE_WARN=int(config.get('BIAS_LUMINANCE_VARIANCE_WARN'))
BIAS_FRAME_COUNT_MIN=int(config.get('BIAS_FRAME_COUNT_MIN'))
FLAT_FRAME_COUNT_MIN=int(config.get('FLAT_FRAME_COUNT_MIN'))
DARK_FRAME_COUNT_MIN=int(config.get('DARK_FRAME_COUNT_MIN'))

parser=argparse.ArgumentParser()

parser.add_argument("--dir", '-d', help="working directory", type=str, default="./")
args=parser.parse_args()

parser.add_argument("--darks", '-k', help="dark frames directory", type=str, default=args.dir + '/darks')
parser.add_argument("--flats", '-f', help="flat frames directory", type=str, default=args.dir + '/flats')
parser.add_argument("--biases", '-b', help="bias frames directory", type=str, default=args.dir + '/biases')
parser.add_argument("--lights", '-l', help="light frames directory", type=str, default=args.dir + '/lights')
args=parser.parse_args()

flat_frames = [args.dir + '/flats/' + f for f in os.listdir(args.flats)]
dark_frames = [args.dir + '/darks/' + f for f in os.listdir(args.darks)]
bias_frames = [args.dir + '/biases/' + f for f in os.listdir(args.biases)]
light_frames = [args.dir + '/lights/' + f for f in os.listdir(args.lights)]

errors = []
successes = []
warnings = []

light_tags = get_required_exif_tags(light_frames[0])
flat_tags = get_required_exif_tags(flat_frames[0])
dark_tags = get_required_exif_tags(dark_frames[0])
bias_tags = {}
if (len(bias_frames) > 0):
    bias_tags = get_required_exif_tags(bias_frames[0])

def verify_darks():
    print('Verifying dark frames...')
    if (len(dark_frames) >= DARK_FRAME_COUNT_MIN):
        successes.append(f"Dark frame count: {len(dark_frames)}")
    elif (len(dark_frames) > 0):
        warnings.append(f"Dark frame count low: {len(dark_frames)} (Suggested: {DARK_FRAME_COUNT_MIN})")
    else:
        errors.append("Dark frames missing")
        return
    
    try:
        validate_sibling_frame_exif_tags(dark_frames)
        successes.append("Dark frame sibling settings match")
    except Exception as e:
        errors.append(e)

    lum_val = get_luminance_value(dark_frames[0])
    if (lum_val <= DARK_LUMINANCE_VARIANCE):
        successes.append(f"Dark frame luminance: {str(lum_val)}")
    elif (lum_val > DARK_LUMINANCE_VARIANCE and lum_val < DARK_LUMINANCE_VARIANCE_WARN):
        warnings.append(f"Dark frame luminance is most likely too high: {str(lum_val)}")
    else:
        errors.append(f"Dark frame luminance is most likely too high: {str(lum_val)}")
    
    # ENSURES AMBIENT TEMPERATURES MATCH
    with ExifToolHelper() as et:
        dark_temp = round(et.get_tags(dark_frames[0], tags=["AmbientTemperature"])[0].get('EXIF:AmbientTemperature'))
        light_temp = round(et.get_tags(light_frames[0], tags=["AmbientTemperature"])[0].get('EXIF:AmbientTemperature'))
        temps_match = abs(dark_temp - light_temp) <= AMBIENT_TEMP_VARIANCE
        temps_close = abs(dark_temp - light_temp) <= AMBIENT_TEMP_VARIANCE_WARN
        if (temps_match == True):
            successes.append("Dark and Light frames have matching ambient temperatures")
        elif (temps_close == True):
            warnings.append("Dark and Light frames temperatures might be too different")
        else:
            errors.append("Dark and Light frames have ambient temperatures too far apart")
    
    # ENSURES TAKEN WITH SAME EXPOSURE SETTINGS
    if (dark_tags.get('ShutterSpeedValue') == light_tags.get('ShutterSpeedValue') and dark_tags.get('BulbDuration') == light_tags.get('BulbDuration') and dark_tags.get('ISO') == light_tags.get('ISO')):
        successes.append("Dark and Light frames were taken with same exposure settings")
    else:
        errors.append("Dark and Light frames were taken with different exposure settings")

def verify_flats():
    print('Verifying flat frames...')
    if (len(flat_frames) >= FLAT_FRAME_COUNT_MIN):
        successes.append(f"Flat frame count: {len(flat_frames)}")
    elif (len(flat_frames) > 0):
        warnings.append(f"Flat frame count low: {len(flat_frames)} (Suggested: {FLAT_FRAME_COUNT_MIN})")
    else:
        errors.append("Flat frames missing")
        return
    
    try:
        validate_sibling_frame_exif_tags(flat_frames)
        successes.append("Flat frame sibling settings match")
    except Exception as e:
        errors.append(e)

    # Verify flats have same ISO and Aperture as Lights
    if (flat_tags.get('ApertureValue') != flat_tags.get('ApertureValue')):
        errors.append('Flat and Light Aperture values do not match')
    elif (flat_tags.get('ShutterSpeedValue') != flat_tags.get('ShutterSpeedValue')):
        errors.append('Flat and Light Shutterspeeds do not match')
    elif (flat_tags.get('BulbDuration') != flat_tags.get('BulbDuration')):
        errors.append('Flat and Light Shutterspeeds do not match')
    else:
        successes.append('Flat and Light exposure settings match')

def verify_biases():
    print('Verifying bias frames...')
    if (len(bias_frames) >= BIAS_FRAME_COUNT_MIN):
        successes.append(f"Bias frame count: {len(bias_frames)}")
    elif (len(bias_frames) > 0):
        warnings.append(f"Bias frame count low: {len(bias_frames)} (Suggested: {BIAS_FRAME_COUNT_MIN})")
    else:
        errors.append("Bias frames missing")
        return

    try:
        validate_sibling_frame_exif_tags(bias_frames)
        successes.append("Bias frame sibling settings match")
    except Exception as e:
        errors.append(e)

    lum_val = get_luminance_value(bias_frames[0])
    if (lum_val <= BIAS_LUMINANCE_VARIANCE):
        successes.append(f"Bias frame luminance: {str(lum_val)}")
    elif (lum_val > BIAS_LUMINANCE_VARIANCE and lum_val < BIAS_LUMINANCE_VARIANCE_WARN):
        warnings.append(f"Bias frame luminance is most likely too high: {str(lum_val)}")
    else:
        errors.append(f"Bias frame luminance is most likely too high: {str(lum_val)}")
    
    if (bias_tags.get('ShutterSpeedValue') != bias_tags.get('ShutterSpeedValue')):
        errors.append('Bias and Light Shutterspeeds do not match')
    elif (bias_tags.get('BulbDuration') != bias_tags.get('BulbDuration')):
        errors.append('Bias and Light Shutterspeeds do not match')
    else:
        successes.append('Bias and Light exposure settings match')
    
def verify_lights():
    print('Verifying light frames...')
    try:
        validate_sibling_frame_exif_tags(light_frames)
        successes.append("Light frame sibling settings match")
    except Exception as e:
        errors.append(e)

def validate_frames():
    try:
        verify_lights()
        verify_darks()
        verify_flats()
        if (len(bias_tags.items) > 0):
            verify_biases()
    except Exception as e:
        print(e)

    # FINAL OUTPUT
    if (len(successes) != 0):
        print(f"{Fore.GREEN}► Sucessful checks{Fore.RESET}")
        for i in successes:
            print(f"    {Fore.GREEN}✓{Fore.RESET} {i}")
    if (len(warnings) != 0):
        print(f"{Fore.YELLOW}► Warnings{Fore.RESET}")
        for i in warnings:
            print(f"    {Fore.YELLOW}⚠{Fore.RESET}  {str(i)}")
    if (len(errors) != 0):
        print(f"{Fore.RED}► Failed checks{Fore.RESET}")
        for i in errors:
            print(f"    {Fore.RED}⊠{Fore.RESET} {i}")
