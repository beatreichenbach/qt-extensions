import logging
from functools import wraps
from typing import Callable

from PySide2 import QtWidgets

from qt_extensions import theme


def init() -> None:
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger(__package__).setLevel(logging.DEBUG)


def gui(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> int:
        init()
        app = QtWidgets.QApplication()
        theme.apply_theme(theme.one_dark_two)
        result = func(*args, **kwargs)
        return app.exec_()

    return wrapper
