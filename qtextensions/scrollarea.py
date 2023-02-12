import logging

from PySide2 import QtCore, QtGui, QtWidgets


class VerticalScrollArea(QtWidgets.QScrollArea):
    # ScrollArea widget that has a minimum width based on its content

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.viewport().installEventFilter(self)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.viewport() and event.type() == QtCore.QEvent.LayoutRequest:
            if self.widget():
                min_width = self.widget().minimumSizeHint().width()
                if self.verticalScrollBar().isVisible():
                    min_width += self.verticalScrollBar().sizeHint().width()
                self.setMinimumWidth(min_width)
        return super().eventFilter(watched, event)

    def update(self) -> None:
        min_width = self.widget().minimumSizeHint().width()
        self.setMinimumWidth(min_width)

    def sizeHint(self) -> QtCore.QSize:
        widget = self.widget() or self
        return widget.sizeHint()
