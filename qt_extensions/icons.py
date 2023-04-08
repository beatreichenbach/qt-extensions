# initially I had https://github.com/marella/material-design-icons/ added as a submodule
# but zip files of the repo on github does not include submodules.
# to go around this issue icons are compiled to qt resource file using compile_icons.py

import enum
import logging
import sys

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtGui import QIcon, QPalette

from qt_extensions import icons_resource


def fill_pixmap(pixmap: QtGui.QPixmap, color: QtGui.QColor) -> QtGui.QPixmap:
    pixmap = QtGui.QPixmap(pixmap)
    painter = QtGui.QPainter(pixmap)
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return pixmap


class MaterialIcon(QIcon):
    class Style(enum.Enum):
        FILLED = 'filled'
        OUTLINED = 'outlined'
        ROUND = 'round'
        SHARP = 'sharp'
        TWO_TONE = 'two-tone'

    def __init__(self, name: str, style: Style | None = None) -> None:
        super().__init__()

        # set pixmap
        if style is None:
            style = MaterialIcon.Style.OUTLINED

        self._path = f':/material-design-icons/svg/{style.value}/{name}.svg'
        self._pixmap = QtGui.QPixmap(self._path)

        self._init_colors()

    def _init_colors(self) -> None:
        # get palette colors
        app = QtWidgets.QApplication.instance()
        palette = app.palette()
        self._colors = {
            QIcon.On: {
                QIcon.Normal: None,
                QIcon.Active: None,
                QIcon.Disabled: None,
                QIcon.Selected: None,
            },
            QIcon.Off: {
                QIcon.Normal: palette.color(QPalette.Normal, QPalette.WindowText),
                QIcon.Active: None,
                QIcon.Disabled: palette.color(QPalette.Disabled, QPalette.WindowText),
                QIcon.Selected: None,
            },
        }

        for state, modes in self._colors.items():
            for mode, color in modes.items():
                if color is not None:
                    pixmap = fill_pixmap(self._pixmap, color)
                    self.addPixmap(pixmap, mode, state)

    def pixmap(
        self,
        size: QtCore.QSize | None = None,
        mode: QtGui.QIcon.Mode = QtGui.QIcon.Normal,
        state: QtGui.QIcon.State = QtGui.QIcon.Off,
        color: QtGui.QColor | None = None,
    ) -> QtGui.QPixmap:
        if size is None:
            size = self._pixmap.size()
        if color is None:
            color = self._colors[state][mode]
            if color is None:
                color = self._colors[QIcon.Off][QIcon.Normal]
        pixmap = QtGui.QIcon(self._path).pixmap(size)
        return fill_pixmap(pixmap, color)
