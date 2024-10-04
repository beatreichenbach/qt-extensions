from __future__ import annotations

import enum
import importlib

from PySide2 import QtWidgets, QtGui


class MaterialIcon(QtGui.QIcon):
    class Style(enum.Enum):
        OUTLINED = 'outlined'
        ROUNDED = 'rounded'
        SHARP = 'sharp'

    OUTLINED = Style.OUTLINED
    ROUNDED = Style.ROUNDED
    SHARP = Style.SHARP

    def __init__(
        self, name: str, style: Style = Style.OUTLINED, fill: bool = False
    ) -> None:
        super().__init__()

        import_resource(style)

        self.name = name
        file_name = f'{name}_fill1_24px.svg' if fill else f'{name}_24px.svg'
        self._path = (
            f':/material-design-icons/symbols/web/{name}/'
            f'materialsymbols{style.value}/{file_name}'
        )
        self._pixmap = QtGui.QPixmap(self._path)

        self._init_colors()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name})'

    def _init_colors(self) -> None:
        palette = QtWidgets.QApplication.instance().palette()
        role = QtGui.QPalette.WindowText
        self._color_normal = palette.color(QtGui.QPalette.Normal, role)
        self.set_color(self._color_normal, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._color_disabled = palette.color(QtGui.QPalette.Disabled, role)
        self.set_color(self._color_disabled, QtGui.QIcon.Disabled, QtGui.QIcon.Off)

    def add_icon(
        self,
        icon: QtGui.QIcon,
        mode: QtGui.QIcon.Mode = QtGui.QIcon.Normal,
        state: QtGui.QIcon.State = QtGui.QIcon.Off,
    ):
        if isinstance(icon, MaterialIcon):
            pixmap = icon._pixmap
        else:
            pixmap = icon.pixmap(self._pixmap.size())
        self.addPixmap(pixmap, mode, state)

    def pixmap(
        self,
        extent: int = 0,
        mode: QtGui.QIcon.Mode = QtGui.QIcon.Normal,
        state: QtGui.QIcon.State = QtGui.QIcon.Off,
        color: QtGui.QColor | None = None,
    ) -> QtGui.QPixmap:
        if extent:
            # NOTE: QPixmap caused crashes.
            # pixmap = QtGui.QPixmap(self._path).scaledToWidth(extent)
            pixmap = QtGui.QIcon(self._path).pixmap(extent)
        else:
            pixmap = self._pixmap

        if color is None:
            if state == QtGui.QIcon.Off and mode == QtGui.QIcon.Disabled:
                color = self._color_disabled
            else:
                color = self._color_normal
        return fill_pixmap(pixmap, color)

    def set_color(
        self,
        color: QtGui.QColor,
        mode: QtGui.QIcon.Mode = QtGui.QIcon.Normal,
        state: QtGui.QIcon.State = QtGui.QIcon.Off,
    ):
        pixmap = fill_pixmap(self._pixmap, color)
        self.addPixmap(pixmap, mode, state)


def import_resource(style: MaterialIcon.Style) -> None:
    """
    Imports the resource for Qt, separated by style to not load unneeded SVGs.
    """
    importlib.import_module(f'.icons_{style.value}', package='qt_extensions.resources')


def fill_pixmap(pixmap: QtGui.QPixmap, color: QtGui.QColor) -> QtGui.QPixmap:
    """
    Return a copy of 'pixmap' filled with 'color'.
    """
    pixmap = QtGui.QPixmap(pixmap)
    painter = QtGui.QPainter(pixmap)
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return pixmap
