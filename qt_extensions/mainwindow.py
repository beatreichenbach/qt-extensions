from __future__ import annotations

import dataclasses
import typing
from collections import OrderedDict
from collections.abc import Sequence
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets
from qt_material_icons import MaterialIcon

from qt_extensions import helper
from qt_extensions.typeutils import cast, basic


@dataclasses.dataclass()
class DockWidgetState:
    current_index: int
    widgets: tuple[tuple[str, str], ...]
    detachable: bool
    auto_delete: bool
    is_center_widget: bool
    geometry: QtCore.QRect = QtCore.QRect()
    flags: int = 0


@dataclasses.dataclass()
class SplitterState:
    sizes: tuple[int, ...]
    orientation: QtCore.Qt.Orientation
    states: tuple[StateType, ...]
    geometry: QtCore.QRect = QtCore.QRect()
    flags: int = 0


StateType = typing.TypeVar(
    'StateType', bound=typing.Union[DockWidgetState, SplitterState, None]
)


@dataclasses.dataclass()
class RegisteredWidget:
    cls: type
    title: str
    unique: bool


class DockTabBar(QtWidgets.QTabBar):
    detach_started: QtCore.Signal = QtCore.Signal(int)
    detach_moved: QtCore.Signal = QtCore.Signal(QtCore.QPoint)
    detach_finished: QtCore.Signal = QtCore.Signal(QtCore.QPoint)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._drag_index = None
        self._detaching = False

        self.tabBarClicked.connect(self._tab_bar_click)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._detaching:
            # mouse is pressed down and a tab is detached
            self.detach_moved.emit(event.pos())
        elif not self.rect().contains(event.pos()) and self._drag_index is not None:
            # a tab is about to be detached
            self.detach_started.emit(self._drag_index)
            self._detaching = True
        else:
            # no tab is detached
            # this must only be called when _detaching == False
            # undocking tabs while mouse move events are being processed leads to
            # crashes because of the tab's QPainter events
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._detaching:
            self.detach_finished.emit(event.pos())
        self._detaching = False
        self._drag_index = None

    def tabInserted(self, index: int) -> None:
        self._update_tab(index)

    def _request_tab_close(self, action: QtWidgets.QAction) -> None:
        for index in range(self.count()):
            button = self.tabButton(index, QtWidgets.QTabBar.RightSide)
            if action == button.defaultAction():
                self.tabCloseRequested.emit(index)
                return

    def _tab_bar_click(self, index: int) -> None:
        self._drag_index = index

    def _update_tab(self, index: int) -> None:
        close_icon = MaterialIcon('close')
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        icon_size = QtCore.QSize(size, size)

        close_action = QtWidgets.QAction()
        close_action.setIcon(close_icon)
        close_action.triggered.connect(partial(self._request_tab_close, close_action))
        close_button = QtWidgets.QToolButton(self)
        close_button.setAutoRaise(True)
        close_button.setDefaultAction(close_action)
        close_button.setMaximumSize(icon_size)
        self.setTabButton(index, QtWidgets.QTabBar.RightSide, close_button)


class Splitter(QtWidgets.QSplitter):
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

        self.tabBar().detach_started.connect(self._detach_start)
        self.tabBar().detach_moved.connect(self._detach_move)
        self.tabBar().detach_finished.connect(self._detach_finish)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.update_window_title)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # since widgets are stored in window._widgets, trigger garbage collection
        for widget in self.widgets().values():
            widget.deleteLater()
        super().closeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        if self.isWindow():
            self.center()
        super().showEvent(event)

    def tabRemoved(self, index: int) -> None:
        self.try_delete()

    def add_dock_widget(
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
                    parent.insertWidget(index, splitter)
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

    def center(self) -> None:
        if not self.dock_window:
            return

        center = self.dock_window.geometry().center()
        x = center.x() - (self.width() // 2)
        y = center.y() - (self.height() // 2)
        self.move(x, y)

    def close_tab(self, index: int) -> None:
        widget = self.widget(index)
        self.removeTab(index)
        # since widgets are stored in window._widgets, trigger garbage collection
        if widget is not None:
            widget.deleteLater()

    def detach(self, index: int, interactive=False) -> None:
        if index not in range(self.count()) or not self.detachable:
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
        self._drag_widget.float()
        # adding tab after setting window flag, triggers window title update
        self._drag_widget.addTab(widget, title)
        self._drag_widget.setGeometry(geometry)
        if interactive:
            self._drag_widget.setWindowOpacity(0.5)
        self._drag_widget.raise_()
        self._drag_widget.show()
        self._drag_widget.activateWindow()

    def dock_rects(self) -> dict[QtCore.Qt.DockWidgetArea, QtCore.QRect]:
        if not self._hidden:
            rects = {area: self._dock_rect(area) for area in self.dock_areas}
        else:
            rects = {}
        return rects

    def dock_preview_rect(self, area: QtCore.Qt.DockWidgetArea) -> QtCore.QRect:
        return self._dock_rect(area, 0.5)

    def float(self) -> None:
        self.setWindowFlag(QtCore.Qt.Tool, True)

    def update_window_title(self, index: int) -> None:
        if self.window() != self.dock_window:
            self.window().setWindowTitle(self.tabText(index))

    def try_delete(self) -> None:
        if self.auto_delete and not self.count():
            # this widget must not be deleted during a drag event
            # to get around this the widget or its parent will have their opacity set
            # to 0 or be hidden
            self._hidden = True
            if self._drag_widget:
                self._hide_recursively(self)
            else:
                self.deleteLater()

    def widgets(self) -> OrderedDict[str, QtWidgets.QWidget]:
        widgets = OrderedDict()
        for i in range(self.count()):
            widgets[self.tabText(i)] = self.widget(i)
        return widgets

    def _detach_start(self, index: int) -> None:
        self.detach(index, interactive=True)

    def _detach_move(self, position: QtCore.QPoint) -> None:
        if self._drag_widget:
            position = QtGui.QCursor().pos()
            height = self.style().pixelMetric(QtWidgets.QStyle.PM_TitleBarHeight)
            offset = position - QtCore.QPoint(height / 2, height / 2)
            self._drag_widget.move(offset)
            self.dock_window.add_dock_widget(self._drag_widget, position, True)

    def _detach_finish(self, position: QtCore.QPoint) -> None:
        if self._drag_widget:
            self._drag_widget.setWindowOpacity(1)
            position = QtGui.QCursor().pos()
            self.dock_window.add_dock_widget(self._drag_widget, position)
        self._drag_widget = None
        self.try_delete()

    def _dock_rect(
        self, area: QtCore.Qt.DockWidgetArea, factor: float = 0.2
    ) -> QtCore.QRect:
        size = self.size() * factor
        rect = self.rect()
        if area == QtCore.Qt.LeftDockWidgetArea:
            rect.setWidth(size.width())
            return rect
        elif area == QtCore.Qt.RightDockWidgetArea:
            right = rect.right()
            rect.setWidth(size.width())
            rect.moveRight(right)
            return rect
        elif area == QtCore.Qt.TopDockWidgetArea:
            rect.setHeight(size.height())
            return rect
        elif area == QtCore.Qt.BottomDockWidgetArea:
            bottom = rect.bottom()
            rect.setHeight(size.height())
            rect.moveBottom(bottom)
            return rect
        elif area == QtCore.Qt.NoDockWidgetArea:
            return rect
        return rect

    def _hide_recursively(self, widget) -> None:
        # hides the top most widget without deleting it
        if widget.isWindow():
            widget.setWindowOpacity(0)
        else:
            parent = widget.parent()
            if isinstance(parent, Splitter) and parent.count() == 1:
                # if splitter's only child is self, make it invisible
                self._hide_recursively(parent)
            elif parent:
                # if there are other children,
                # it's safe to hide as splitter will not auto delete
                widget.hide()


class DockWindow(QtWidgets.QWidget):
    widget_added: QtCore.Signal = QtCore.Signal(QtWidgets.QWidget)
    dock_widget_added: QtCore.Signal = QtCore.Signal(DockWidget)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.center_widget: DockWidget | None = None
        self.registered_widgets: dict[str, RegisteredWidget] = {}

        self._widgets: dict[str, QtWidgets.QWidget] = {}
        self._rubber_band: QtWidgets.QRubberBand | None = None

        self._init_rubber_band()
        self._init_ui()

    def _init_rubber_band(self) -> None:
        self._rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle)
        self._rubber_band.setParent(self)
        self._rubber_band.destroyed.connect(self._init_rubber_band)

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # center widget
        self.center_splitter = Splitter(QtCore.Qt.Vertical)
        self.center_widget = self._add_protected_dock_widget(self.center_splitter)
        self.layout().addWidget(self.center_splitter)

        self.layout().setStretch(0, 1)

    def add_dock_widget(
        self, widget: DockWidget, position: QtCore.QPoint, simulate: bool = False
    ) -> None:
        # add a widget at global position
        dock_rects = self._dock_rects()

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
                        target.add_dock_widget(widget, area)
                    return
                else:
                    self._rubber_band.hide()

    def create_dock_widget(
        self,
        widget: QtWidgets.QWidget | type | str,
        title: str | None = None,
    ) -> DockWidget:
        # helper function to turn QWidgets into DockWidgets
        for title_, widget_ in self._widgets.items():
            if widget == widget_:
                unique_title, widget_instance = title_, widget_
                break
        else:
            unique_title, widget_instance = self._add_widget(widget, title)

        dock_widget = DockWidget(dock_window=self)
        dock_widget.addTab(widget_instance, unique_title)
        self.dock_widget_added.emit(dock_widget)

        return dock_widget

    def dock_widgets(self) -> tuple[DockWidget, ...]:
        # return all DockWidgets under this window. They are sorted in a manner
        # that makes sense for checking dock areas.
        children = self.findChildren(DockWidget)
        # floating widgets have the Tool window flag and are always in front:
        children = sorted(children, key=DockWidget.isWindow)
        # list deepest nested children first
        children = reversed(children)

        return tuple(children)

    def register_widget(
        self, cls: type, title: str | None = None, unique: bool = True
    ) -> RegisteredWidget:
        if title is None:
            title = helper.title(cls.__name__)

        key = cls.__name__
        if key not in self.registered_widgets:
            registered_widget = RegisteredWidget(cls, title, unique)
            self.registered_widgets[key] = registered_widget
        return self.registered_widgets[key]

    def unregister_widget(self, cls: type | str) -> None:
        # returns true if widget was found and unregistered, false if not found
        key = cls.__name__ if not isinstance(cls, type) else cls
        self.registered_widgets.pop(key, None)

    def set_window_state(self, state: dict) -> None:
        values = {'geometry': None, 'widgets': []}
        values.update(state)

        self.set_widget_states(values['widgets'])

        try:
            geometry = cast(QtCore.QRect, values['geometry'])
            self.setGeometry(geometry)
        except TypeError:
            pass

    def set_widget_states(self, states: Sequence[dict]) -> None:
        # store all current widgets for layout
        widgets = dict(self._widgets)
        # unparent all widgets to clean up layout
        for widget in widgets.values():
            widget.setParent(None)
            widget.close()

        states = cast(tuple[StateType, ...], states)
        self._set_widget_states(states, self, widgets)

        # remove unused widgets
        for title, widget in widgets.items():
            widget.deleteLater()

    def state(self) -> dict:
        state = {'geometry': self.geometry(), 'widgets': self.widget_states()}
        state = basic(state)
        return state

    def widget_title(self, widget: QtWidgets.QWidget) -> str | None:
        for k, v in self._widgets.items():
            if widget == v:
                return k

    def widget_states(
        self, widget: QtWidgets.QWidget | None = None
    ) -> tuple[StateType, ...]:
        states = []

        if widget is None:
            children = self.children()
        else:
            children = (widget.widget(i) for i in range(widget.count()))

        for child in children:
            if isinstance(child, Splitter):
                state = SplitterState(
                    sizes=tuple(child.sizes()),
                    orientation=child.orientation(),
                    states=self.widget_states(child),
                )

            elif isinstance(child, DockWidget):
                widgets = tab_widget_classes(child)
                state = DockWidgetState(
                    current_index=child.currentIndex(),
                    widgets=widgets,
                    detachable=child.detachable,
                    auto_delete=child.auto_delete,
                    is_center_widget=(child == self.center_widget),
                )
            else:
                # ignore other widget classes
                continue

            if child.isWindow():
                state.geometry = child.geometry()
                state.flags = int(child.windowFlags())

            states.append(state)
        return tuple(states)

    # noinspection PyMethodMayBeStatic
    def focus_widget(self, widget: QtWidgets.QWidget) -> None:
        parent = widget.parent()
        while parent is not None:
            if isinstance(parent, QtWidgets.QTabWidget):
                break
            parent = parent.parent()
        index = parent.indexOf(widget)
        parent.setCurrentIndex(index)

        window = widget.window()
        window.setWindowState(
            (window.windowState() & ~QtCore.Qt.WindowMinimized) | QtCore.Qt.WindowActive
        )
        window.raise_()
        window.activateWindow()

    def _add_protected_dock_widget(self, parent: Splitter) -> DockWidget:
        dock_widget = DockWidget(self, self)
        dock_widget.auto_delete = False
        parent.addWidget(dock_widget)
        parent.setCollapsible(parent.count() - 1, False)
        return dock_widget

    def _add_widget(
        self, widget: QtWidgets.QWidget | type | str, title: str | None = None
    ) -> tuple[str, QtWidgets.QWidget]:
        # adds a new widget to the window
        if isinstance(widget, str):
            key = widget
            registered_widget = self.registered_widgets.get(key)
            if not registered_widget:
                raise ValueError(f'widget for {repr(key)} has not been registered')
            widget = registered_widget.cls()
        else:
            if isinstance(widget, type):
                cls = widget
                widget = cls()
            else:
                cls = type(widget)
            registered_widget = self.register_widget(cls, title)
            key = cls.__name__

        # check if widget is unique
        if registered_widget.unique:
            if any(type(widget) is type(w) for w in self._widgets.values()):
                raise ValueError(
                    f'Widget {repr(key)} can only be added once to DockWindow '
                )
        # get title
        if title is None:
            title = registered_widget.title

        titles = tuple(self._widgets.keys())
        unique_title = helper.unique_name(title, titles)

        widget.destroyed.connect(lambda: self._widget_destroy(widget))
        self._widgets[unique_title] = widget
        self.widget_added.emit(widget)

        return unique_title, widget

    def _dock_rects(
        self,
    ) -> OrderedDict[DockWidget, dict[QtCore.Qt.DockWidgetArea, QtCore.QRect]]:
        rects = OrderedDict()
        widgets = self.dock_widgets()
        for widget in widgets:
            rects[widget] = widget.dock_rects()
        return rects

    def _set_widget_states(
        self,
        states: Sequence[StateType],
        parent: QtWidgets.QWidget,
        widgets: dict[str, QtWidgets.QWidget],
    ) -> None:
        # inner loop for setting widget states
        # removes widgets from widgets dict that have been added to the new layout

        for i, state in enumerate(states):
            # create widget
            if isinstance(state, SplitterState):
                if parent == self:
                    splitter = self.center_splitter
                    splitter.setOrientation(state.orientation)
                else:
                    splitter = Splitter(state.orientation)
                self._set_widget_states(state.states, splitter, widgets)
                splitter.setSizes(state.sizes)

                widget = splitter
            elif isinstance(state, DockWidgetState):
                if state.is_center_widget:
                    dock_widget = self.center_widget
                else:
                    dock_widget = DockWidget(self)
                    dock_widget.detachable = state.detachable
                    dock_widget.auto_delete = state.auto_delete

                for title, cls_name in state.widgets:
                    # remove widget from dictionary to keep track of
                    # which widgets have been re-parented
                    widget = widgets.pop(title, None)

                    if widget is None:
                        try:
                            title, widget = self._add_widget(cls_name)
                        except ValueError:
                            continue
                    dock_widget.addTab(widget, title)

                dock_widget.setCurrentIndex(state.current_index)

                widget = dock_widget
            else:
                continue

            # parent widget
            if isinstance(parent, Splitter):
                if parent.widget(i) is not None:
                    # not replacing widget with itself prevents warnings
                    if parent.widget(i) != widget:
                        parent.replaceWidget(i, widget)
                        widget.setParent(parent)
                        widget.show()
                else:
                    parent.addWidget(widget)
            else:
                widget.show()

            # set window
            if state.flags:
                flags = QtCore.Qt.WindowFlags(state.flags)
                widget.setWindowFlags(flags)
                widget.setGeometry(state.geometry)
                widget.show()

    def _widget_destroy(self, widget: QtWidgets.QWidget) -> None:
        # NOTE: At the point destroyed() is emitted, the widget isn't a QWidget anymore,
        #   just a QObject (as destroyed() is emitted from QObject)
        title = self.widget_title(widget)
        if title is not None:
            # self.widget_removed.emit(widget)
            self._widgets.pop(title)


def area_orientation(area: QtCore.Qt.DockWidgetArea) -> QtCore.Qt.Orientation:
    if area in (QtCore.Qt.LeftDockWidgetArea, QtCore.Qt.RightDockWidgetArea):
        return QtCore.Qt.Horizontal
    elif area in (QtCore.Qt.TopDockWidgetArea, QtCore.Qt.BottomDockWidgetArea):
        return QtCore.Qt.Vertical


def tab_widget_classes(widget: QtWidgets.QTabWidget) -> tuple[tuple[str, str], ...]:
    # widgets is a tuple [title, cls.__name__]
    widgets = []
    for i in range(widget.count()):
        widgets.append((widget.tabText(i), type(widget.widget(i)).__name__))
    return tuple(widgets)
