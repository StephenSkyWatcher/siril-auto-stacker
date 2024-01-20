from exiftool import ExifToolHelper

def get_required_exif_tags(img):
    _tags = {}
    with ExifToolHelper() as et:
        _tags = et.get_tags(img, tags=["AmbientTemperature", "ShootingMode", "ExposureMode", "ImageSize", "LensModel", "ISO", "FocalLength", "ApertureValue", "ShutterSpeedValue", "BulbDuration"])[0]
    return {
        "ShootingMode": _tags.get('Composite:ShootingMode'),
        "ExposureMode": _tags.get('EXIF:ExposureMode'),
        "ImageSize": _tags.get('Composite:ImageSize'),
        "LensModel": _tags.get('MakerNotes:LensModel'),
        "ISO": _tags.get('EXIF:ISO'),
        "FocalLength": _tags.get('EXIF:FocalLength'),
        "ApertureValue": _tags.get('EXIF:ApertureValue'),
        "ShutterSpeedValue": _tags.get('EXIF:ShutterSpeedValue'),
        "BulbDuration": _tags.get('MakerNotes:BulbDuration'),
        "AmbientTemperature": _tags.get('EXIF:AmbientTemperature')
    }

def get_user_comment(img):
    _tags = {}
    with ExifToolHelper() as et:
        _tags = et.get_tags(img, tags=["UserComment"])[0]
    return _tags.get('EXIF:UserComment')
    # return {
    #     "ShootingMode": _tags.get('Composite:ShootingMode'),
    #     "ExposureMode": _tags.get('EXIF:ExposureMode'),
    #     "ImageSize": _tags.get('Composite:ImageSize'),
    #     "LensModel": _tags.get('MakerNotes:LensModel'),
    #     "ISO": _tags.get('EXIF:ISO'),
    #     "FocalLength": _tags.get('EXIF:FocalLength'),
    #     "ApertureValue": _tags.get('EXIF:ApertureValue'),
    #     "ShutterSpeedValue": _tags.get('EXIF:ShutterSpeedValue'),
    #     "BulbDuration": _tags.get('MakerNotes:BulbDuration'),
    #     "AmbientTemperature": _tags.get('EXIF:AmbientTemperature')
    # }
