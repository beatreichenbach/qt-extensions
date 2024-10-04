from PySide2 import QtCore, QtGui, QtWidgets


class ElideLabel(QtWidgets.QLabel):
    def __init__(self, text='', parent=None) -> None:
        super().__init__(text, parent)

        self._text = text

    def minimumSizeHint(self) -> QtCore.QSize:
        size = super().minimumSizeHint()
        size.setWidth(size.height())
        return size

    def setText(self, text: str) -> None:
        super().setText(text)
        self._text = self.text()

    def _update_text(self) -> None:
        font_metrics = self.fontMetrics()
        width = self.contentsRect().width()
        text = font_metrics.elidedText(self._text, QtCore.Qt.ElideRight, width)
        super().setText(text)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_text()
