from __future__ import annotations

import dataclasses
import sys

from PySide2 import QtWidgets, QtGui
from PySide2.QtGui import QPalette, QColor

from qt_extensions.typeutils import deep_field


@dataclasses.dataclass
class ColorRoles:
    # https://m2.material.io/design/color/the-color-system.html
    critical: QtGui.QColor = deep_field(QtGui.QColor(236, 64, 122))
    error: QtGui.QColor = deep_field(QtGui.QColor(239, 83, 80))
    warning: QtGui.QColor = deep_field(QtGui.QColor(255, 167, 38))
    info: QtGui.QColor = deep_field(QtGui.QColor(66, 165, 245))
    success: QtGui.QColor = deep_field(QtGui.QColor(102, 187, 106))


@dataclasses.dataclass
class ColorScheme:
    base_bg: QtGui.QColor = deep_field(QtGui.QColor(255, 255, 255))
    base_mg: QtGui.QColor = deep_field(QtGui.QColor(240, 240, 240))
    base_fg: QtGui.QColor = deep_field(QtGui.QColor(245, 245, 245))

    text: QtGui.QColor = deep_field(QtGui.QColor(0, 0, 0))
    primary: QtGui.QColor = deep_field(QtGui.QColor(0, 120, 215))

    black: QtGui.QColor = deep_field(QtGui.QColor(20, 20, 20))


class Color(QtGui.QColor):
    def __new__(cls, role: str):
        if role == 'primary':
            return QtGui.QPalette().color(QtGui.QPalette.Highlight)

        roles = ColorRoles()
        try:
            return getattr(roles, role)
        except AttributeError:
            return QtGui.QColor(role)


def apply_scheme(scheme: ColorScheme, palette: QtGui.QPalette):
    # auto generate Light, MidLight, Mid, Dark, Shadow colors
    h, s, button_v, a = scheme.base_mg.getHsvF()
    light_v = scheme.base_bg.valueF()
    if scheme.text.value() < scheme.base_mg.value():
        #  text < shadow < dark < mid < button < midlight < light
        black_v = scheme.black.valueF()
    else:
        # shadow < light < midlight < button < mid < dark < text
        black_v = scheme.text.valueF()

    dark = QtGui.QColor.fromHsvF(h, s, lerp(black_v, button_v, 0.35), a)
    mid = QtGui.QColor.fromHsvF(h, s, lerp(black_v, button_v, 0.65), a)
    mid_light = QtGui.QColor.fromHsvF(h, s, lerp(button_v, light_v, 0.5), a)

    # base
    palette.setColor(QtGui.QPalette.Window, scheme.base_mg)
    palette.setColor(QtGui.QPalette.WindowText, scheme.text)
    palette.setColor(QtGui.QPalette.Base, scheme.base_bg)
    palette.setColor(QtGui.QPalette.AlternateBase, scheme.base_fg)
    palette.setColor(QtGui.QPalette.ToolTipBase, scheme.base_bg)
    palette.setColor(QtGui.QPalette.ToolTipText, scheme.text)
    palette.setColor(QtGui.QPalette.PlaceholderText, dark)
    palette.setColor(QtGui.QPalette.Text, scheme.text)
    palette.setColor(QtGui.QPalette.Button, scheme.base_mg)
    palette.setColor(QtGui.QPalette.ButtonText, scheme.text)
    palette.setColor(QtGui.QPalette.BrightText, invert_value(scheme.text))

    palette.setColor(QtGui.QPalette.Highlight, scheme.primary)
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))

    palette.setColor(QtGui.QPalette.Link, scheme.primary.darker(125))
    palette.setColor(QtGui.QPalette.LinkVisited, scheme.primary.darker(125))

    palette.setColor(QtGui.QPalette.Light, scheme.base_bg)
    palette.setColor(QtGui.QPalette.Midlight, mid_light)
    palette.setColor(QtGui.QPalette.Mid, mid)
    palette.setColor(QtGui.QPalette.Dark, dark)
    palette.setColor(QtGui.QPalette.Shadow, scheme.black)

    # disabled
    palette.setColor(QPalette.Disabled, QtGui.QPalette.WindowText, dark)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.Base, scheme.base_mg)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.AlternateBase, scheme.base_mg)

    palette.setColor(QPalette.Disabled, QtGui.QPalette.PlaceholderText, dark)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.Text, dark)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.Button, scheme.base_fg)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.ButtonText, dark)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.BrightText, scheme.base_bg)

    palette.setColor(QPalette.Disabled, QPalette.Highlight, scheme.base_mg)
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, scheme.base_fg)

    palette.setColor(QPalette.Disabled, QtGui.QPalette.Link, dark)
    palette.setColor(QPalette.Disabled, QtGui.QPalette.LinkVisited, dark)


def apply_theme(
    scheme: ColorScheme | None = None,
    style: str = 'Fusion',
    app: QtWidgets.QApplication | None = None,
) -> None:
    if app is None:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    palette = app.palette()
    app.setStyle(style)

    if not scheme:
        return
    apply_scheme(scheme, palette)
    app.setPalette(palette)

    if scheme.text.value() > scheme.base_mg.value():
        # QAbstractItemView alternating row color fix
        item_view_palette = QPalette(palette)
        item_view_palette.setColor(
            QPalette.AlternateBase, palette.color(QPalette.Window)
        )
        app.setPalette(item_view_palette, 'QAbstractItemView')  # noqa


def invert_value(color: QtGui.QColor) -> QtGui.QColor:
    h, s, v, a = color.getHsvF()
    color = QtGui.QColor.fromHsvF(h, s, 1 - v, a)
    return color


def lerp(a: float, b: float, t: float) -> float:
    return (1 - t) * a + t * b


modern_dark = ColorScheme(
    base_bg=QtGui.QColor(42, 42, 42),
    base_mg=QtGui.QColor(53, 53, 53),
    base_fg=QtGui.QColor(66, 66, 66),
    text=QtGui.QColor(200, 200, 200),
    primary=QColor(42, 165, 218),
)

modern_light = ColorScheme(
    base_bg=QtGui.QColor(255, 255, 255),
    base_mg=QtGui.QColor(242, 242, 242),
    base_fg=QtGui.QColor(230, 235, 240),
    text=QtGui.QColor(0, 0, 0),
    primary=QtGui.QColor(51, 105, 214),
)

monokai = ColorScheme(
    base_bg=QtGui.QColor(41, 42, 46),
    base_mg=QtGui.QColor(50, 51, 56),
    base_fg=QtGui.QColor(60, 61, 66),
    text=QtGui.QColor(206, 209, 217),
    primary=QtGui.QColor(73, 174, 238),
)

one_dark_two = ColorScheme(
    base_bg=QtGui.QColor(33, 37, 43),
    base_mg=QtGui.QColor(40, 44, 52),
    base_fg=QtGui.QColor(57, 62, 71),
    text=QtGui.QColor(230, 230, 230),
    primary=QtGui.QColor(113, 185, 244),
)
