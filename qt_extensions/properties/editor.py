import dataclasses
import itertools
import os
from collections.abc import Iterable
import typing
from typing_extensions import Self

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions import helper
from qt_extensions.scrollarea import VerticalScrollArea
from qt_extensions.properties import PropertyWidget
from qt_extensions.box import CollapsibleBox
from qt_extensions.typeutils import cast


class PropertyToolTip(QtWidgets.QFrame):
    def __init__(
        self, widget: PropertyWidget, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, palette.color(QtGui.QPalette.Base))
        self.setPalette(palette)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        title = QtWidgets.QLabel(widget.label, self)
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        self.layout().addWidget(title)

        separator = QtWidgets.QFrame(self)
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout().addWidget(separator)

        typ = type(widget).__name__.replace('Property', '')
        detail = QtWidgets.QLabel(f'Property: {widget.name} ({typ})', self)
        self.layout().addWidget(detail)

        tooltip = QtWidgets.QLabel(widget.tooltip, self)
        # tooltip.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        tooltip.setWordWrap(True)
        tooltip.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.layout().addWidget(tooltip)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.hide()


class PropertyLabel(QtWidgets.QLabel):
    def __init__(
        self, widget: PropertyWidget, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(widget.label, parent)

        self._tooltip: PropertyToolTip | None = None
        self._widget = widget

    def enterEvent(self, event: QtCore.QEvent) -> None:
        if self._widget.tooltip:
            QtCore.QTimer.singleShot(600, self.show_tooltip)
        super().enterEvent(event)

    def show_tooltip(self):
        global_position = QtGui.QCursor.pos()
        if self.geometry().contains(self.parent().mapFromGlobal(global_position)):
            if self._tooltip is None:
                self._tooltip = PropertyToolTip(self._widget, parent=self.window())
            self._tooltip.move(self.window().mapFromGlobal(global_position))
            self._tooltip.show()


class PropertyEditor(VerticalScrollArea):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.__dict__['form'] = PropertyForm()
        self.setWidget(self.form)

    def __getattr__(self, item: typing.Any) -> typing.Any:
        return getattr(self.form, item)

    def __setattr__(self, key: str, value: typing.Any) -> None:
        setattr(self.form, key, value)


class PropertyForm(QtWidgets.QWidget):
    actions_changed: QtCore.Signal = QtCore.Signal(list)
    property_changed: QtCore.Signal = QtCore.Signal(PropertyWidget)

    # require unique names in the whole hierarchy
    unique_hierarchical_names: bool = False

    # when querying widgets or values, should these values be in their own hierarchy
    create_hierarchy: bool = True

    def __init__(
        self,
        name: str | None = None,
        root: Self | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._widgets: dict[str, PropertyWidget] = {}

        self.name = name
        self.root = root or self

        self.setLayout(QtWidgets.QGridLayout())

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)})'

    @property
    def grid_layout(self) -> QtWidgets.QGridLayout:
        layout = self.layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise RuntimeError('Layout needs to be QGridLayout')
        return layout

    def actionEvent(self, event: QtGui.QActionEvent) -> None:
        super().actionEvent(event)
        self.actions_changed.emit(self.actions())

    def add_property(self, widget: PropertyWidget) -> PropertyWidget:
        name = widget.name
        self._validate_name(name)

        self._widgets[name] = widget

        layout = self.grid_layout
        row = layout.rowCount() - 1

        # label
        if widget.label:
            label = PropertyLabel(widget, self)
            layout.addWidget(label, row=row, column=0)
            widget.enabled_changed.connect(label.setEnabled)
            widget.enabled_changed.emit(widget.isEnabled())

        # widget
        layout.addWidget(widget, row=row, column=1)
        widget.value_changed.connect(lambda: self.property_changed.emit(widget))

        self._update_stretch()
        return widget

    def add_group(
        self,
        name: str,
        label: str = None,
        collapsible: bool = False,
        style: CollapsibleBox.Style = None,
    ) -> Self:
        form = self._create_form(name)
        form.property_changed.connect(self.property_changed.emit)
        label = label or helper.title(name)
        group = CollapsibleBox(label, collapsible, style)
        if collapsible:
            group.collapsed = True

        group.setLayout(QtWidgets.QVBoxLayout())
        group.layout().setContentsMargins(0, 0, 0, 0)
        group.layout().setSpacing(0)
        group.layout().addWidget(form)

        # update CollapsibleBox with actions for the menu
        form.actions_changed.connect(group.set_actions)

        self.add_widget(group)
        return form

    def add_tab_group(
        self, names: Iterable[str], labels: Iterable[str] = None
    ) -> QtWidgets.QTabWidget:
        group = QtWidgets.QTabWidget(self)
        group.tabs = {}
        labels = labels or []
        for name, label in itertools.zip_longest(names, labels):
            form = self._create_form(name)
            label = label or helper.title(name)
            group.addTab(form, label)
            group.tabs[name] = form

        self.add_widget(group)
        return group

    def add_separator(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame(self)
        line.setFixedHeight(1)
        line.setFrameShape(QtWidgets.QFrame.StyledPanel)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.add_widget(line)
        return line

    def add_widget(
        self, widget: QtWidgets.QWidget, column: int = 0, column_span: int = 2
    ) -> QtWidgets.QWidget:
        layout = self.grid_layout
        row = layout.rowCount() - 1
        layout.addWidget(
            widget, row=row, column=column, rowSpan=1, columnSpan=column_span
        )
        self._update_stretch()
        return widget

    def add_layout(self, layout: QtWidgets.QLayout) -> QtWidgets.QLayout:
        grid_layout = self.grid_layout
        row = grid_layout.rowCount() - 1
        grid_layout.addLayout(layout, row=row, column=0, rowSpan=1, columnSpan=2)
        self._update_stretch()
        return layout

    def boxes(
        self, layout: QtWidgets.QLayout | None = None
    ) -> dict[CollapsibleBox, ...]:
        # create nested dict of all boxes
        if layout is None:
            layout = self.grid_layout

        boxes = {}
        for index in range(layout.count()):
            widget = layout.itemAt(index).widget()
            if isinstance(widget, CollapsibleBox):
                if widget.layout():
                    children = self.boxes(widget.layout())
                    boxes[widget] = children
            elif isinstance(widget, PropertyForm):
                children = widget.boxes()
                boxes.update(children)
        return boxes

    def reset(self, widgets: dict[str, PropertyWidget] | None = None) -> None:
        if widgets is None:
            widgets = self.widgets()

        for widget in widgets.values():
            if isinstance(widget, PropertyWidget):
                widget.value = widget.default
            elif isinstance(widget, dict):
                self.reset(widget)

    def set_state(self, state: dict) -> None:
        values = {'collapsed_boxes': []}
        values.update(state)
        collapsed_boxes = values['collapsed_boxes']
        self._set_collapsed_boxes(collapsed_boxes)

    def set_values(
        self,
        values: dict,
        widgets: dict[str, PropertyWidget] | None = None,
        attr: str = 'value',
    ) -> None:
        if widgets is None:
            widgets = self.widgets()
        for key, value in values.items():
            if key not in widgets:
                continue
            widget = widgets[key]
            if isinstance(widget, dict):
                self.set_values(value, widget, attr)
            else:
                setattr(widget, attr, value)

    def state(self) -> dict:
        collapsed_boxes = self._collapsed_boxes()
        state = {'collapsed_boxes': collapsed_boxes}
        return state

    def values(self) -> dict[str, typing.Any]:
        # create nested dictionary of all property values
        values = {}
        for name, widget in self._widgets.items():
            if isinstance(widget, self.__class__):
                if widget.create_hierarchy:
                    values[name] = widget.values()
                else:
                    values.update(widget.values())
            else:
                values[name] = widget.value
        return values

    def widgets(self) -> dict[str, PropertyWidget]:
        # create nested dictionary of all property widgets
        widgets = {}
        for name, widget in self._widgets.items():
            if isinstance(widget, self.__class__):
                if widget.create_hierarchy:
                    widgets[name] = widget.widgets()
                else:
                    widgets.update(widget.widgets())
            else:
                widgets[name] = widget
        return widgets

    def _collapsed_boxes(
        self, boxes: dict[CollapsibleBox, ...] | None = None
    ) -> list[str]:
        # returns a list of all collapsed boxes
        # child boxes are separated by dot 'parent.child'
        if boxes is None:
            boxes = self.boxes()

        collapsed_boxes = []
        for box, children in boxes.items():
            if box.collapsed:
                collapsed_boxes.append(box.title)

            child_boxes = self._collapsed_boxes(children)
            child_boxes = ['.'.join([box.title, child]) for child in child_boxes]
            collapsed_boxes.extend(child_boxes)
        return collapsed_boxes

    def _create_form(self, name) -> Self:
        self._validate_name(name)

        form = self.__class__(name=name, root=self)
        self._widgets[name] = form

        return form

    def _hierarchical_names(self) -> list[str]:
        # generate a flat list of all child widget names
        names = []
        for name, widget in self._widgets.items():
            if isinstance(widget, self.__class__):
                names.extend(widget.hierarchical_names())
            else:
                names.append(name)
        return names

    def _set_collapsed_boxes(
        self, collapsed_boxes: list[str], boxes: dict[CollapsibleBox, ...] | None = None
    ) -> None:
        # collapses the boxes in the list, child boxes are separated by dot 'parent.child'

        if boxes is None:
            boxes = self.boxes()

        for box, children in boxes.items():
            box.collapsed = box.title in collapsed_boxes
            child_boxes = [
                b.split('.', 1)[-1]
                for b in collapsed_boxes
                if b.split('.', 1)[0] == box.title
            ]
            self._set_collapsed_boxes(child_boxes, children)

    def _update_stretch(self) -> None:
        layout = self.grid_layout
        layout.setRowStretch(layout.rowCount() - 1, 0)
        layout.setRowStretch(layout.rowCount(), 1)

    def _validate_name(self, name: str) -> None:
        if name is None:
            raise ValueError(f'Cannot add widget with name {name}')

        # check if name is unique relative to root
        if self.root.unique_hierarchical_names:
            hierarchical_names = self.root._hierarchical_names()
        else:
            hierarchical_names = list(self._widgets.keys())
        if name in hierarchical_names:
            raise ValueError(f'Cannot add widget {name} (name already exists)')


__all__ = ['PropertyEditor']
