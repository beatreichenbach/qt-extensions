from PySide2 import QtWidgets, QtGui, QtCore


class ResizeGrip(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.can_resize_vertical = True
        self.can_resize_horizontal = False

        self._resizing = False
        self._min_size = None
        self._start_position = QtCore.QPoint()
        self._start_size = QtCore.QSize()
        self._start_size_policy = None
        self._start_max_size = None

        self.setCursor(QtCore.Qt.SizeFDiagCursor)
        self.reset()
        parent.installEventFilter(self)

    @property
    def min_size(self) -> QtCore.QSize:
        if self._min_size is None:
            min_size = self.parent().minimumSize()
            min_size_hint = self.parent().minimumSizeHint()
            min_width = max(min_size.width(), min_size_hint.width(), self.width())
            min_height = max(min_size.height(), min_size_hint.height(), self.height())
            self._min_size = QtCore.QSize(min_width, min_height)
        return self._min_size

    def changeEvent(self, event: QtCore.QEvent) -> None:
        if event.type() == QtCore.QEvent.ParentChange and self.parent():
            self.reset()

    def eventFilter(self, obj, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Resize and obj == self.parent():
            self.reposition()
            self.resize_scroll_bars()
            return False
        return super().eventFilter(obj, event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        opt = QtWidgets.QStyleOptionSizeGrip()
        opt.initFrom(self)
        opt.corner = QtCore.Qt.BottomRightCorner
        self.style().drawControl(QtWidgets.QStyle.CE_SizeGrip, opt, painter, self)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.reset()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)
        self._resizing = True
        self._start_size = self.parent().geometry().size()
        self._start_position = event.globalPos()
        if self._start_size_policy is None:
            self._start_size_policy = self.parent().sizePolicy()
        if self._start_max_size is None:
            self._start_max_size = self.parent().maximumSize()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._resizing:
            delta = event.globalPos() - self._start_position
            if self.can_resize_horizontal:
                width = self._start_size.width() + delta.x()
                width = max(width, self.min_size.width())
                self.parent().setFixedWidth(width)

            if self.can_resize_vertical:
                height = self._start_size.height() + delta.y()
                height = max(height, self.min_size.height())
                self.parent().setFixedHeight(height)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self._resizing = False

    def reset(self) -> None:
        # reset size
        size = self.parent().style().pixelMetric(QtWidgets.QStyle.PM_SizeGripSize)
        self.setFixedSize(size, size)

        # reset sizePolicy
        if self._start_size_policy is not None:
            policy = self._start_size_policy
            self._start_size_policy = None
            self.parent().setSizePolicy(policy)

        # reset maximumSize
        if self._start_max_size is not None:
            max_size = self._start_max_size
            self._start_max_size = None
            self.parent().setMaximumSize(max_size)

        # reset minimumSize
        self.parent().setMinimumSize(self.parent().minimumSizeHint())
        self._min_size = None

    def reposition(self) -> None:
        geometry = self.geometry()
        geometry.moveBottomRight(self.parent().contentsRect().bottomRight())
        self.setGeometry(geometry)

    def resize_scroll_bars(self) -> None:
        if isinstance(self.parent(), QtWidgets.QAbstractScrollArea):
            size = self.parent().contentsRect().size() - self.size()
            self.parent().horizontalScrollBar().setMaximumWidth(size.width())
            self.parent().verticalScrollBar().setMaximumHeight(size.height())
