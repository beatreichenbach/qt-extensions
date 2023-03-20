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


class Palette(QPalette):
    def __init__(
        self, scheme: ColorScheme | None = None, palette: QPalette | None = None
    ) -> None:
        super().__init__(palette)

        if not scheme:
            return
        # base
        self.setColor(QPalette.WindowText, scheme.bright2)
        self.setColor(QPalette.Button, scheme.dark3)
        self.setColor(QPalette.Light, scheme.bright2)
        self.setColor(QPalette.Midlight, scheme.medium3)
        self.setColor(QPalette.Dark, scheme.dark1)
        self.setColor(QPalette.Text, scheme.bright2)
        self.setColor(QPalette.BrightText, scheme.bright2)
        self.setColor(QPalette.ButtonText, scheme.bright2)
        self.setColor(QPalette.Base, scheme.dark2)
        self.setColor(QPalette.Window, scheme.dark3)
        self.setColor(QPalette.Shadow, scheme.black1)
        self.setColor(QPalette.Highlight, scheme.primary)
        self.setColor(QPalette.HighlightedText, scheme.bright2)
        self.setColor(QPalette.Link, scheme.secondary)
        self.setColor(QPalette.AlternateBase, scheme.medium1)
        self.setColor(QPalette.ToolTipBase, scheme.dark3)
        self.setColor(QPalette.ToolTipText, scheme.bright2)
        self.setColor(QPalette.LinkVisited, scheme.medium2)

        # disabled
        self.setColor(QPalette.Disabled, QPalette.WindowText, scheme.bright1)
        self.setColor(QPalette.Disabled, QPalette.Text, scheme.bright1)
        self.setColor(QPalette.Disabled, QPalette.ButtonText, scheme.bright1)
        self.setColor(QPalette.Disabled, QPalette.Highlight, scheme.medium2)
        self.setColor(QPalette.Disabled, QPalette.HighlightedText, scheme.bright1)


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


def apply_theme(
    scheme: ColorScheme | None = None,
    style: str = 'Fusion',
    app: QtWidgets.QApplication | None = None,
) -> None:
    if app is None:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    palette = Palette(scheme, palette=app.palette())
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
