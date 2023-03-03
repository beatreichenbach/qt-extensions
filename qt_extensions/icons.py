# initially I had https://github.com/marella/material-design-icons/ added as a submodule
# but zip files of the repo on github does not include submodules.
# to go around this icons are compile to qt resource file using compile_icons.py

import enum
import logging
import sys

from PySide2 import QtWidgets, QtGui
from PySide2.QtGui import QIcon, QPalette

from qt_extensions import icons_resources


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
        # dir_name = str(style.value)

        # file_path = os.path.join(svg_path, dir_name, f'{name}.svg')
        # if not os.path.isfile(file_path):
        #     raise FileNotFoundError(file_path)

        self._pixmap = QtGui.QPixmap(
            f':/material-design-icons/svg/{style.value}/{name}.svg'
        )

        # get palette colors
        app = QtWidgets.QApplication.instance()
        palette = app.palette()
        colors = {
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

        self.init_colors(colors)

    def init_colors(self, colors: dict) -> None:
        for state, modes in colors.items():
            for mode, color in modes.items():
                if color:
                    self.set_color(color, mode, state)

    def set_color(
        self, color: QtGui.QColor, mode: QtGui.QIcon.Mode, state: QtGui.QIcon.State
    ) -> None:
        pixmap = QtGui.QPixmap(self._pixmap)
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        self.addPixmap(pixmap, mode, state)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()

    icon = MaterialIcon('folder', MaterialIcon.Style.FILLED)
    logging.debug(icon)
    button = QtWidgets.QPushButton()
    button.setIcon(icon)
    button.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
