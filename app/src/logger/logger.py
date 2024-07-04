import logging
import inspect
import pprint
from datetime import datetime, timedelta
from .color import *

# https://pygments.org/docs/styles/#ansiterminalstyle
from pygments import highlight
from pygments.style import Style, ansicolors
from pygments.styles import get_all_styles, get_style_by_name
from pygments.token import Token
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

"""
print(list(get_all_styles()))
print(list(get_style_by_name('emacs')))
material
autumn
arduino
dracula
"""

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def pprint_color(obj) -> None:
    """Pretty-print in color."""
    print(
        highlight(
            pprint.pformat(obj, indent=1, depth=4, width=80, compact=True),
            PythonLexer(),
            Terminal256Formatter(style=get_style_by_name("dracula")),
        ),
        end="",
    )


class Logger(logging.Logger):
    format_string = f"%(message)s"

    def inspector(self):
        return inspect.stack()[2].filename, inspect.stack()[2].lineno

    def __init__(self, name):
        super().__init__(name)
        formatter = logging.Formatter(self.format_string, datefmt=TIME_FORMAT)
        shandler = logging.StreamHandler()
        shandler.setFormatter(formatter)
        shandler.setLevel(logging.NOTSET)
        self.handler = shandler
        self.handlers.append(shandler)

    def log(self, msg, *args, **kwargs):
        colored_message = f"{msg}"
        super().debug(colored_message, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        time = datetime.now().strftime(TIME_FORMAT)
        fileName, lineno = self.inspector()
        colored_message = f"{fg.MAGENTA}[DEBUG]{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}\n{style.DIM}{msg}{style.RESET_ALL}"
        super().debug(colored_message, *args, **kwargs)

    def config(self, c, *args, **kwargs):
        colored_message = f"{fg.CYAN}{style.BRIGHT}[{c.name}]{bg.RESET}{style.RESET_ALL} {fg.CYAN}{c.get()} {style.RESET_ALL}{fg.RESET}{style.RESET_ALL}"
        super().info(colored_message, *args, **kwargs)
        pprint_color(c.options())

    def action(self, name, msg, *args, **kwargs):
        colored_message = (
            f"{fg.GREEN}[{name}]{fg.RESET} {fg.WHITE}{msg}{style.RESET_ALL}"
        )
        super().info(colored_message, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        time = datetime.now().strftime(TIME_FORMAT)
        fileName, lineno = self.inspector()
        colored_message = f"{time} {fg.GREEN}[INFO] {msg}{fg.RESET} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}"
        super().info(colored_message, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        time = datetime.now().strftime(TIME_FORMAT)
        colored_message = (
            f"{fg.YELLOW}[WARN]{fg.RESET} {time} {fg.YELLOW}{msg}{fg.RESET}"
        )
        super().warning(colored_message, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        time = datetime.now().strftime(TIME_FORMAT)
        fileName, lineno = self.inspector()
        colored_message = f"{fg.RED}[ERROR] {fg.RED}{msg}{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}"
        super().error(colored_message, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        time = datetime.now().strftime(TIME_FORMAT)
        colored_message = f"{time} {fg.RED}{style.BRIGHT}'[CRITICAL] {style.RESET_ALL}\n{fg.RED}{msg}{fg.RESET}"
        super().critical(colored_message, *args, **kwargs)

# def json(self, msg, *args, **kwargs):
#     time = datetime.now().strftime(TIME_FORMAT)
#     fileName, lineno = self.inspector()
#     super().info(
#         f"{fg.BLUE}[JSON]{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}"
#     )
#     pprint_color(msg)

# def time(self, *args, **kwargs):
#     super().debug(datetime.now().strftime("%H:%M:%S"), *args, **kwargs)
