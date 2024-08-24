from __future__ import annotations

from PySide2 import QtCore, QtWidgets


class VerticalScrollArea(QtWidgets.QScrollArea):
    """
    ScrollArea widget that has a minimum width based on its content.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        viewport = QtWidgets.QWidget(self)
        viewport.installEventFilter(self)
        self.setViewport(viewport)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.viewport() and event.type() == QtCore.QEvent.LayoutRequest:
            if self.widget():
                min_width = self.widget().minimumSizeHint().width()
                if self.verticalScrollBar().isVisible():
                    min_width += self.verticalScrollBar().sizeHint().width()
                self.setMinimumWidth(min_width)
        return super().eventFilter(watched, event)

    def setWidget(self, widget: QtWidgets.QWidget) -> None:
        super().setWidget(widget)
        widget.setAutoFillBackground(False)

    def sizeHint(self) -> QtCore.QSize:
        widget = self.widget() or super()
        return widget.sizeHint()

    def update(self) -> None:
        if self.widget():
            min_width = self.widget().minimumSizeHint().width()
            self.setMinimumWidth(min_width)
