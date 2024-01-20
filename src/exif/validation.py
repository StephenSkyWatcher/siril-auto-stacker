from . import get_required_exif_tags

# Validates all files within a given group
# match the first image in that group
def validate_sibling_frame_exif_tags(frames):
    first_tags = get_required_exif_tags(frames[0])
    for index in range(len(frames)):
        cur_tags = get_required_exif_tags(frames[index])
        for k, v in cur_tags.items():
            if (first_tags.get(k) != v):
                raise Exception(f"{frames[index]} doesnt match {str(k)} of {v}")