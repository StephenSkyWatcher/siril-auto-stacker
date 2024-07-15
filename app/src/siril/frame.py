import os
from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class Frame:
    def __init__(self, name: str, dir: str, process_dir: str, stacked_prefix: str) -> None:
        self.name = name
        self.dir = dir
        self.process_dir = process_dir
        self.stacked_name = f"{stacked_prefix}{name}"

    def process_url(self) -> str:
        return f"{self.process_dir}"
