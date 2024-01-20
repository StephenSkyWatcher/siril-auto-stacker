import argparse
import os
from dotenv import load_dotenv
from src.validation import validate_frames
from src.siril import stack
from src.exif import get_required_exif_tags, get_user_comment

load_dotenv()
parser=argparse.ArgumentParser()

parser.add_argument("--dir", '-d', help="working directory", type=str, default="./")
args=parser.parse_args()

first_light_frame = [args.dir + '/lights/' + f for f in os.listdir(args.dir + '/lights')][0]
light_tags = get_required_exif_tags(first_light_frame)

# Start Processes
try:
    # TODO: Fix logging and raise exception on invalid
    # validate_frames()
    
    stack(
        wd=args.dir,
        iso=light_tags.get('ISO')
    )

    # TODO: Move files to /mnt/storage/....

except Exception as e:
    print("VALIDATION FAILURE")
    print(e)
