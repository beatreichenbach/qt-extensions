from PySide2 import QtCore, QtGui, QtWidgets


class VerticalScrollArea(QtWidgets.QScrollArea):
    # ScrollArea widget that has a minimum width based on its content

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.verticalScrollBar():
            if (
                event.type() in (QtCore.QEvent.Show, QtCore.QEvent.Hide)
                and self.widget()
            ):
                min_width = self.widget().minimumSizeHint().width()
                if event.type() == QtCore.QEvent.Show:
                    min_width += self.verticalScrollBar().sizeHint().width()
                self.setMinimumWidth(min_width)
        return super().eventFilter(watched, event)

    def update(self) -> None:
        min_width = self.widget().minimumSizeHint().width()
        self.setMinimumWidth(min_width)

    def sizeHint(self) -> QtCore.QSize:
        widget = self.widget() or self
        return widget.sizeHint()
