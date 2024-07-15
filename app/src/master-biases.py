from .camera import Camera
from .logger import Logger as _Logger

Logger = _Logger(__name__)

camera = Camera()

try:
    camera.capture_master_biases(isos=None)
    camera.close()
except Exception as e:
    camera.close()
    Logger.error(e)
