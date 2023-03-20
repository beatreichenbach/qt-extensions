import enum

from PySide2 import QtWidgets, QtGui


class Button(QtWidgets.QPushButton):
    class Style(enum.IntFlag):
        NONE = 0
        PRIMARY = enum.auto()
        # SECONDARY = enum.auto()

    def __init__(
        self,
        text: str = '',
        icon: QtGui.QIcon | None = None,
        style: Style = Style.NONE,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(text=text, parent=parent)
        if icon:
            self.setIcon(icon)
        if style == Button.Style.PRIMARY:
            palette = self.palette()
            palette.setColor(
                QtGui.QPalette.Button,
                palette.color(QtGui.QPalette.Highlight).darker(125),
            )
            palette.setColor(
                QtGui.QPalette.ButtonText,
                palette.color(QtGui.QPalette.ButtonText).lighter(125),
            )
            self.setPalette(palette)

        minimum_height = (
            self.style().pixelMetric(QtWidgets.QStyle.PM_ButtonIconSize) * 2
        )
        self.setMinimumHeight(minimum_height)
