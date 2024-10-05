from __future__ import annotations

from PySide2 import QtWidgets, QtGui, QtCore
from qt_material_icons import MaterialIcon

from qt_extensions import theme


class BaseButton(QtWidgets.QPushButton):
    def __init__(
        self,
        text: str = '',
        icon: QtGui.QIcon | None = None,
        color: QtGui.QColor | str | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(text=text, parent=parent)

        if icon:
            self.setIcon(icon)

        self._icon_size = self.style().pixelMetric(QtWidgets.QStyle.PM_ButtonIconSize)
        self._icon_size = self.iconSize().width()
        self._icon_off = None
        self._icon_on = None
        self._contents_margins = QtCore.QSize(0, 0)
        self._palette_off = None
        self._palette_on = None

        self.set_color(color)

        self.toggled.connect(self._checked_change)

    def sizeHint(self) -> QtCore.QSize:
        size_hint = super().sizeHint()
        size_hint += self._contents_margins
        return size_hint

    def setIcon(self, icon: QtGui.QIcon, on: bool = False) -> None:
        if on:
            if self._palette_on and isinstance(icon, MaterialIcon):
                icon.set_color(self._palette_on.color(QtGui.QPalette.ButtonText))
            self._icon_on = icon
        else:
            self._icon_off = icon
            super().setIcon(icon)

    def set_color(self, color: QtGui.QColor | str | None) -> None:
        palette = self.palette()
        self._palette_off = self.palette()

        if isinstance(color, str):
            color = theme.Color(color)

        if color is None:
            button_color = QtGui.QPalette().color(QtGui.QPalette.Button)
            text_color = QtGui.QPalette().color(QtGui.QPalette.ButtonText)
        else:
            button_color = color.darker(125)
            text_color = self.palette().color(QtGui.QPalette.ButtonText)
            if text_color.valueF() > button_color.valueF() * 0.5:
                text_color = text_color.lighter(150)
            else:
                text_color = text_color.darker(150)

        palette.setColor(QtGui.QPalette.Button, button_color)
        palette.setColor(
            QtGui.QPalette.Disabled, QtGui.QPalette.Button, button_color.darker(150)
        )

        palette.setColor(QtGui.QPalette.Normal, QtGui.QPalette.ButtonText, text_color)
        self.setPalette(palette)
        self._palette_on = palette

    def set_margins(self, w: float | None = None, h: float | None = None) -> None:
        if w is not None:
            self._contents_margins.setWidth(w * self._icon_size)
        if h is not None:
            self._contents_margins.setHeight(h * self._icon_size / 2)

    def _checked_change(self, checked: bool) -> None:
        # BUG: fusion style does not recognize On/Off for QIcons
        # https://bugreports.qt.io/browse/QTBUG-82110
        icon = self._icon_on if checked else self._icon_off
        if icon is not None:
            super().setIcon(icon)


class Button(BaseButton):
    def __init__(
        self,
        text: str = '',
        icon: QtGui.QIcon | None = None,
        color: QtGui.QColor | str | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(text, icon, color, parent)

        self.set_margins(w=2)
        self.setMinimumHeight(self._icon_size * 2)


class CheckBoxButton(BaseButton):
    def __init__(
        self,
        text: str = '',
        icon: QtGui.QIcon | None = None,
        color: QtGui.QColor | str | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(text, icon, color, parent)

        self.setCheckable(True)
        self.set_margins(w=0.5)

        self.setIcon(MaterialIcon('check_box_outline_blank', fill=True))
        self.setIcon(MaterialIcon('check_box'), True)

    def _checked_change(self, checked: bool) -> None:
        super()._checked_change(checked)
        self._update_color()

    def _update_color(self) -> None:
        if self._palette_on is None:
            return
        if self.isChecked():
            self.setPalette(self._palette_on)
        else:
            self.setPalette(self._palette_off)

    def set_color(self, color: QtGui.QColor | str | None) -> None:
        super().set_color(color)
        self._update_color()
