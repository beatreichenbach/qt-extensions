import dataclasses
import sys
from PySide2 import QtWidgets, QtGui
from PySide2.QtGui import QPalette, QColor


@dataclasses.dataclass
class ColorScheme:
    primary: QColor
    secondary: QColor
    black1: QColor
    dark1: QColor
    dark2: QColor
    dark3: QColor
    medium1: QColor
    medium2: QColor
    medium3: QColor
    bright1: QColor
    bright2: QColor


def apply_scheme(scheme: ColorScheme, palette: QtGui.QPalette):
    # base
    palette.setColor(QPalette.WindowText, scheme.bright2)
    palette.setColor(QPalette.Button, scheme.dark3)
    palette.setColor(QPalette.Light, scheme.bright2)
    palette.setColor(QPalette.Midlight, scheme.medium3)
    palette.setColor(QPalette.Dark, scheme.dark1)
    palette.setColor(QPalette.Text, scheme.bright2)
    palette.setColor(QPalette.BrightText, scheme.bright2)
    palette.setColor(QPalette.ButtonText, scheme.bright2)
    palette.setColor(QPalette.Base, scheme.dark2)
    palette.setColor(QPalette.Window, scheme.dark3)
    palette.setColor(QPalette.Shadow, scheme.black1)
    palette.setColor(QPalette.Highlight, scheme.primary)
    palette.setColor(QPalette.HighlightedText, scheme.bright2)
    palette.setColor(QPalette.Link, scheme.secondary)
    palette.setColor(QPalette.AlternateBase, scheme.medium1)
    palette.setColor(QPalette.ToolTipBase, scheme.dark3)
    palette.setColor(QPalette.ToolTipText, scheme.bright2)
    palette.setColor(QPalette.LinkVisited, scheme.medium2)

    # disabled
    palette.setColor(QPalette.Disabled, QPalette.WindowText, scheme.bright1)
    palette.setColor(QPalette.Disabled, QPalette.Text, scheme.bright1)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, scheme.bright1)
    palette.setColor(QPalette.Disabled, QPalette.Highlight, scheme.medium2)
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, scheme.bright1)


def apply_theme(
    scheme: ColorScheme | None = None,
    style: str = 'Fusion',
    app: QtWidgets.QApplication | None = None,
) -> None:
    if app is None:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    palette = app.palette()
    apply_scheme(scheme, palette)
    app.setPalette(palette)
    app.setStyle(style)

    # QScrollArea background color fix
    scroll_area_palette = QPalette(palette)
    scroll_area_palette.setColor(QPalette.Window, palette.color(QPalette.AlternateBase))
    app.setPalette(scroll_area_palette, QtWidgets.QScrollArea.__name__)

    # QTabWidget background tab fix
    tab_widget_palette = QPalette(palette)
    tab_widget_palette.setColor(QPalette.Light, palette.color(QPalette.Midlight))
    app.setPalette(tab_widget_palette, QtWidgets.QTabWidget.__name__)

    # QAbstractItemView alternating row color fix
    item_view_palette = QPalette(palette)
    item_view_palette.setColor(QPalette.AlternateBase, palette.color(QPalette.Window))
    app.setPalette(item_view_palette, QtWidgets.QAbstractItemView.__name__)


# Original color palette from https://github.com/gmarull/qtmodern
modern_dark = ColorScheme(
    primary=QColor(42, 165, 218),
    secondary=QColor(38, 126, 163),
    black1=QColor(20, 20, 20),
    dark1=QColor(35, 35, 35),
    dark2=QColor(42, 42, 42),
    dark3=QColor(53, 53, 53),
    medium1=QColor(66, 66, 66),
    medium2=QColor(80, 80, 80),
    medium3=QColor(90, 90, 90),
    bright1=QColor(127, 127, 127),
    bright2=QColor(180, 180, 180),
)

monokai = ColorScheme(
    primary=QColor(73, 174, 238),
    secondary=QColor(62, 113, 179),
    black1=QColor(20, 20, 20),
    dark1=QColor(32, 33, 36),
    dark2=QColor(41, 42, 46),
    dark3=QColor(50, 51, 56),
    medium1=QColor(60, 61, 66),
    medium2=QColor(73, 75, 82),
    medium3=QColor(80, 83, 89),
    bright1=QColor(121, 123, 128),
    bright2=QColor(206, 209, 217),
)
