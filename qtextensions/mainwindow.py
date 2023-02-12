import logging
import sys
from collections import OrderedDict
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets
from qtextensions.icons import MaterialIcon


class DockTabBar(QtWidgets.QTabBar):
    detach_pressed: QtCore.Signal = QtCore.Signal(int)
    detach_moved: QtCore.Signal = QtCore.Signal(QtCore.QPoint)
    detach_released: QtCore.Signal = QtCore.Signal(QtCore.QPoint)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._drag_index = None
        self._detaching = False

        self.tabBarClicked.connect(self.tab_bar_click)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._detaching:
            # mouse is pressed down and a tab is detached
            self.detach_moved.emit(event.pos())
        elif not self.rect().contains(event.pos()) and self._drag_index is not None:
            # a tab is about to be detached
            self.detach_pressed.emit(self._drag_index)
            self._detaching = True
        else:
            # no tab is detached
            # this must only be called when _detaching == False
            # undocking tabs while mouse move events are being processed leads to crashes
            # because of the tab QPainter events
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._detaching:
            self.detach_released.emit(event.pos())
        self._detaching = False
        self._drag_index = None

    def tab_bar_click(self, index: int) -> None:
        self._drag_index = index

    def tabInserted(self, index: int) -> None:
        self.update_tab(index)

    def update_tab(self, index: int) -> None:
        close_icon = MaterialIcon('close')
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        icon_size = QtCore.QSize(size, size)

        close_action = QtWidgets.QAction()
        close_action.setIcon(close_icon)
        close_action.triggered.connect(partial(self.request_tab_close, close_action))
        close_button = QtWidgets.QToolButton(self)
        close_button.setAutoRaise(True)
        close_button.setDefaultAction(close_action)
        close_button.setMaximumSize(icon_size)
        self.setTabButton(index, QtWidgets.QTabBar.RightSide, close_button)

    def request_tab_close(self, action: QtWidgets.QAction) -> None:
        for index in range(self.count()):
            button = self.tabButton(index, QtWidgets.QTabBar.RightSide)
            if action == button.defaultAction():
                self.tabCloseRequested.emit(index)
                return


class Splitter(QtWidgets.QSplitter):
    def __init__(
        self,
        orientation: QtCore.Qt.Orientation,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)
        self.delete = False

    def childEvent(self, event: QtCore.QChildEvent) -> None:
        super().childEvent(event)
        if event.removed() and not self.count():
            self.deleteLater()


class DockWidget(QtWidgets.QTabWidget):
    dock_areas = (
        QtCore.Qt.LeftDockWidgetArea,
        QtCore.Qt.RightDockWidgetArea,
        QtCore.Qt.TopDockWidgetArea,
        QtCore.Qt.BottomDockWidgetArea,
        QtCore.Qt.NoDockWidgetArea,
    )

    def __init__(self, dock_window, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent or dock_window)

        # if parent is None:
        #     self.setWindowFlag(QtCore.Qt.Tool, True)

        self.dock_window = dock_window
        self.detachable = True
        self.auto_delete = True

        self._drag_widget = None
        self._hidden = False

        self._init_ui()

    def _init_ui(self) -> None:
        self.setTabBar(DockTabBar())
        self.setMovable(True)
        self.setTabsClosable(True)

        self.tabBar().detach_pressed.connect(self.detach_press)
        self.tabBar().detach_moved.connect(self.detach_move)
        self.tabBar().detach_released.connect(self.detach_release)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.update_window_title)

    def update_window_title(self, index: int) -> None:
        if self.window() != self.dock_window:
            self.window().setWindowTitle(self.tabText(index))

    def detach_press(self, index: int) -> None:
        self.detach(index)

    def detach_move(self, position: QtCore.QPoint) -> None:
        if self._drag_widget:
            position = QtGui.QCursor().pos()
            height = self.style().pixelMetric(QtWidgets.QStyle.PM_TitleBarHeight)
            offset = position - QtCore.QPoint(height / 2, height / 2)
            self._drag_widget.move(offset)
            self.dock_window.add_widget(self._drag_widget, position, True)

    def detach_release(self, position: QtCore.QPoint) -> None:
        if self._drag_widget:
            self._drag_widget.setWindowOpacity(1)
            position = QtGui.QCursor().pos()
            self.dock_window.add_widget(self._drag_widget, position)
        self._drag_widget = None
        self.try_delete()

    def detach(self, index: int) -> None:
        if index is None or not self.detachable:
            return

        geometry = self.geometry()
        if not self.isWindow():
            top_left = self.parent().mapToGlobal(geometry.topLeft())
            geometry.moveTopLeft(top_left)

        title = self.tabText(index)
        widget = self.widget(index)

        self._drag_widget = self.__class__(self.dock_window)
        self._drag_widget.setParent(self.dock_window)
        # setting window flag after parent creates a window
        self._drag_widget.setWindowFlag(QtCore.Qt.Tool, True)
        # adding tab after setting window flag, triggers window title update
        self._drag_widget.addTab(widget, title)
        self._drag_widget.setGeometry(geometry)
        self._drag_widget.setWindowOpacity(0.5)
        self._drag_widget.raise_()
        self._drag_widget.show()
        self._drag_widget.activateWindow()

    def dock_rect(
        self, area: QtCore.Qt.DockWidgetArea, factor: float = 0.2
    ) -> QtCore.QRect:
        size = self.size() * factor
        rect = self.rect()
        match area:
            case QtCore.Qt.LeftDockWidgetArea:
                rect.setWidth(size.width())
                return rect
            case QtCore.Qt.RightDockWidgetArea:
                right = rect.right()
                rect.setWidth(size.width())
                rect.moveRight(right)
                return rect
            case QtCore.Qt.TopDockWidgetArea:
                rect.setHeight(size.height())
                return rect
            case QtCore.Qt.BottomDockWidgetArea:
                bottom = rect.bottom()
                rect.setHeight(size.height())
                rect.moveBottom(bottom)
                return rect
            case QtCore.Qt.NoDockWidgetArea:
                return rect

    def dock_rects(self) -> dict[QtCore.Qt.DockWidgetArea, QtCore.QRect]:
        if not self._hidden:
            rects = {area: self.dock_rect(area) for area in self.dock_areas}
        else:
            rects = {}
        return rects

    def dock_preview_rect(self, area: QtCore.Qt.DockWidgetArea) -> QtCore.QRect:
        return self.dock_rect(area, 0.5)

    def add_widget(
        self, widget: QtWidgets.QTabWidget, area: QtCore.Qt.DockWidgetArea
    ) -> None:
        if area == QtCore.Qt.NoDockWidgetArea:
            self.addTab(widget.widget(0), widget.tabText(0))
        else:
            parent = self.parent()

            if not parent:
                return

            if self.isWindow() or not isinstance(parent, QtWidgets.QSplitter):
                splitter = Splitter(QtCore.Qt.Vertical)

                if self.isWindow():
                    splitter.setParent(parent)
                    splitter.setWindowFlags(self.windowFlags())
                    splitter.show()
                elif isinstance(parent, QtWidgets.QScrollArea):
                    parent.setWidget(splitter)
                elif isinstance(parent.layout(), QtWidgets.QLayout):
                    parent.layout().replaceWidget(self, splitter)
                    splitter.setParent(parent)
                else:
                    # for other parents it's unknown on how to replace a widget
                    splitter.deleteLater()
                    return

                splitter.setGeometry(self.geometry())
                splitter.addWidget(self)
                parent = splitter

            orientation = area_orientation(area)
            index = parent.indexOf(self)
            if orientation != parent.orientation():
                if parent.count() == 1:
                    parent.setOrientation(orientation)
                else:
                    splitter = Splitter(orientation)
                    parent.replaceWidget(index, splitter)
                    splitter.setParent(parent)
                    splitter.addWidget(self)
                    parent = splitter
                    index = 0

            if area in (
                QtCore.Qt.LeftDockWidgetArea,
                QtCore.Qt.TopDockWidgetArea,
            ):
                parent.insertWidget(index, widget)
            elif area in (
                QtCore.Qt.RightDockWidgetArea,
                QtCore.Qt.BottomDockWidgetArea,
            ):
                parent.insertWidget(index + 1, widget)

    def close_tab(self, index: int) -> None:
        self.removeTab(index)

    def tabRemoved(self, index: int) -> None:
        self.try_delete()

    def try_delete(self) -> None:
        # this widget must not be deleted during a drag event
        # to get around this the widget or its parent will have their opacity set
        # to 0 or be hidden
        if self.auto_delete and not self.count():
            self._hidden = True
            if self._drag_widget:
                self.hide_recursively(self)
            else:
                self.deleteLater()

    def hide_recursively(self, widget) -> None:
        # hides the top most widget without deleting it
        if widget.isWindow():
            widget.setWindowOpacity(0)
        else:
            parent = widget.parent()
            if isinstance(parent, Splitter) and parent.count() == 1:
                # if splitter's only child is self, make it invisible
                self.hide_recursively(parent)
            elif parent:
                # if there are other children,
                # it's safe to hide as splitter will not auto delete
                widget.hide()


class DockWindow(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.center_widget = None

        self._rubber_band = None
        self._init_rubber_band()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.center_widget = DockWidget(self, self)
        self.center_widget.auto_delete = False
        self.layout().addWidget(self.center_widget)
        self.layout().addWidget(QtWidgets.QStatusBar(self))
        self.layout().setStretch(0, 1)

    def _init_rubber_band(self) -> None:
        self._rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle)
        self._rubber_band.setParent(self)
        self._rubber_band.destroyed.connect(self._init_rubber_band)

    def dock_rects(self) -> OrderedDict:
        rects = OrderedDict()
        widgets = self.widgets()
        for widget in widgets:
            rects[widget] = widget.dock_rects()
        return rects

    def widgets(self) -> list[DockWidget]:
        # return all DockWidgets under this window. They are sorted in a manner
        # that makes sense for checking dock areas.
        children = self.findChildren(DockWidget)
        # floating widgets have the Tool window flag and are always in front:
        children = sorted(children, key=DockWidget.isWindow)
        # list deepest nested children first
        children = reversed(children)

        return list(children)

    def add_widget(
        self, widget: DockWidget, position: QtCore.QPoint, simulate: bool = False
    ) -> None:
        dock_rects = self.dock_rects()
        pass
        for target, rects in dock_rects.items():
            if target == widget:
                continue
            target_position = target.mapFromGlobal(position)
            if not target.rect().contains(target_position):
                self._rubber_band.hide()
                continue

            for area, rect in rects.items():
                if rect.contains(target_position):
                    if simulate:
                        preview_rect = target.dock_preview_rect(area)
                        self._rubber_band.setParent(target)
                        self._rubber_band.setGeometry(preview_rect)
                        self._rubber_band.show()
                    else:
                        self._rubber_band.hide()
                        target.add_widget(widget, area)
                    return
                else:
                    self._rubber_band.hide()

    def dockify_widget(
        self,
        widget: QtWidgets.QWidget,
        title: str,
        dock: tuple[DockWidget, QtCore.Qt.DockWidgetArea] | None = None,
    ) -> DockWidget:
        # helper function to turn QWidgets into DockWidgets
        dock_widget = DockWidget(self)
        dock_widget.addTab(widget, title)
        if dock is not None:
            sibling, area = dock
            sibling.add_widget(dock_widget, area)
        else:
            dock_widget.show()
        return dock_widget


def area_orientation(area: QtCore.Qt.DockWidgetArea) -> QtCore.Qt.Orientation:
    if area in (QtCore.Qt.LeftDockWidgetArea, QtCore.Qt.RightDockWidgetArea):
        return QtCore.Qt.Horizontal
    elif area in (QtCore.Qt.TopDockWidgetArea, QtCore.Qt.BottomDockWidgetArea):
        return QtCore.Qt.Vertical


def main():
    from qtextensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.modern_dark)

    window = DockWindow()
    window.title = 'window'
    window.resize(800, 600)

    window.show()

    floating_windows = []
    for i in range(5):
        dock = DockWidget(window)
        title = f'Floating {i}'
        dock.title = title
        dock.addTab(QtWidgets.QPushButton('button'), title)
        floating_windows.append(dock)
        dock.setParent(window)
        dock.setWindowFlag(QtCore.Qt.Tool, True)
        dock.show()

    floating_windows[3].add_widget(floating_windows[4], QtCore.Qt.RightDockWidgetArea)
    window.center_widget.add_widget(floating_windows[4], QtCore.Qt.NoDockWidgetArea)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
