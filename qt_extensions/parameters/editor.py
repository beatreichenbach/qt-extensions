from __future__ import annotations

import itertools
import typing
from collections.abc import Iterable
from functools import partial

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions import helper
from qt_extensions.scrollarea import VerticalScrollArea
from qt_extensions.parameters import ParameterWidget
from qt_extensions.box import CollapsibleBox


class ParameterToggle(QtWidgets.QCheckBox):
    def __init__(self, name: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)})'

    def set_value(self, value: bool) -> None:
        self.setChecked(value)

    def value(self) -> bool:
        return self.isChecked()


class ParameterToolTip(QtWidgets.QFrame):
    def __init__(
        self, widget: ParameterWidget, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, palette.color(QtGui.QPalette.Base))
        self.setPalette(palette)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        title = QtWidgets.QLabel(widget.label(), self)
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        self.layout().addWidget(title)

        separator = QtWidgets.QFrame(self)
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout().addWidget(separator)

        typ = type(widget).__name__.replace('Parameter', '')
        detail = QtWidgets.QLabel(f'Parameter: {widget.name()} ({typ})', self)
        self.layout().addWidget(detail)

        tooltip = QtWidgets.QLabel(widget.tooltip(), self)
        # tooltip.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        tooltip.setWordWrap(True)
        tooltip.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.layout().addWidget(tooltip)

    def focusOutEvent(self, event: QtCore.QEvent) -> None:
        self.hide()

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.hide()


class ParameterLabel(QtWidgets.QLabel):
    def __init__(
        self, widget: ParameterWidget, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(widget.label(), parent)

        self._tooltip: ParameterToolTip | None = None
        self._widget = widget

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.text())})'

    def enterEvent(self, event: QtCore.QEvent) -> None:
        if self._widget.tooltip():
            QtCore.QTimer.singleShot(600, self.show_tooltip)
        super().enterEvent(event)

    def show_tooltip(self):
        global_position = QtGui.QCursor.pos()
        if self.geometry().contains(self.parent().mapFromGlobal(global_position)):
            if self._tooltip is None:
                self._tooltip = ParameterToolTip(self._widget, parent=self.window())
            self._tooltip.move(self.window().mapFromGlobal(global_position))
            self._tooltip.show()


class ParameterTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.tabs: dict[str, ParameterForm] = {}


class ParameterBox(CollapsibleBox):
    def __init__(
        self, title: str, form: ParameterForm, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(title, parent)
        self.form = form

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().addWidget(form)


class ParameterForm(QtWidgets.QWidget):
    actions_changed: QtCore.Signal = QtCore.Signal(list)
    parameter_changed: QtCore.Signal = QtCore.Signal(ParameterWidget)

    # require unique names in the whole hierarchy
    unique_hierarchical_names: bool = False

    # return values as nested dict or flat hierarchy
    create_hierarchy: bool = True

    def __init__(
        self,
        name: str | None = None,
        root: ParameterForm | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._widgets: dict[str, ParameterWidget] = {}

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

    def add_group(self, name: str, label: str = None) -> ParameterBox:
        form = self._create_form(name)
        form.parameter_changed.connect(self.parameter_changed.emit)
        label = label or helper.title(name)
        box = ParameterBox(label, form, self)
        box.set_collapsible(True)
        box.set_collapsed(True)

        # update CollapsibleBox with actions for the menu
        form.actions_changed.connect(box.set_actions)

        self.add_widget(box)
        return box

    def add_layout(
        self,
        layout: QtWidgets.QLayout,
        column: int = 1,
        row_span: int = 1,
        column_span: int = -1,
    ) -> QtWidgets.QLayout:
        grid_layout = self.grid_layout
        row = grid_layout.rowCount() - 1
        grid_layout.addLayout(layout, row, column, row_span, column_span)
        self._update_stretch()
        return layout

    def add_parameter(
        self, widget: ParameterWidget, checkable: bool = False
    ) -> ParameterWidget:
        name = widget.name()
        self._validate_name(name)

        self._widgets[name] = widget

        layout = self.grid_layout
        row = layout.rowCount() - 1

        # label
        if widget.label():
            label = ParameterLabel(widget, self)
            column = 1
            layout.addWidget(label, row, column)
            widget.enabled_changed.connect(label.setEnabled)
            widget.enabled_changed.emit(widget.isEnabled())

        # widget
        column = 2
        layout.addWidget(widget, row, column)
        widget.value_changed.connect(lambda: self.parameter_changed.emit(widget))

        # checkbox
        if checkable:
            checkbox_name = f'{name}_enabled'
            checkbox = ParameterToggle(checkbox_name)
            column = 0
            layout.addWidget(checkbox, row, column)
            checkbox.toggled.connect(partial(self._set_widget_row_enabled, checkbox))
            checkbox.toggled.connect(lambda: self.parameter_changed.emit(checkbox))
            checkbox.set_value(False)
            self._set_widget_row_enabled(checkbox, False)

            self._widgets[checkbox_name] = checkbox

        self._update_stretch()
        return widget

    def add_separator(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame(self)
        line.setFixedHeight(1)
        line.setFrameShape(QtWidgets.QFrame.StyledPanel)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.add_widget(line)
        return line

    def add_tab_group(
        self, names: Iterable[str], labels: Iterable[str] = None
    ) -> ParameterTabWidget:
        tab_widget = ParameterTabWidget(self)
        tab_widget.tabs = {}
        labels = labels or []
        for name, label in itertools.zip_longest(names, labels):
            form = self._create_form(name)
            form.parameter_changed.connect(self.parameter_changed.emit)
            label = label or helper.title(name)
            tab_widget.addTab(form, label)
            tab_widget.tabs[name] = form

        self.add_widget(tab_widget)
        return tab_widget

    def add_widget(
        self, widget: QtWidgets.QWidget, column: int = 1, column_span: int = -1
    ) -> QtWidgets.QWidget:
        layout = self.grid_layout
        row = layout.rowCount() - 1
        row_span = 1
        layout.addWidget(widget, row, column, row_span, column_span)
        self._update_stretch()
        return widget

    def groups(self) -> dict:
        # create hierarchical dict of boxes, groups and tab widgets
        layout = self.grid_layout

        group_dict = {}
        for index in range(layout.count()):
            widget = layout.itemAt(index).widget()
            if isinstance(widget, ParameterBox):
                if widget.form:
                    group_dict[widget] = widget.form.groups()
            elif isinstance(widget, ParameterForm):
                group_dict.update(widget.groups())
            elif isinstance(widget, ParameterTabWidget):
                for form in widget.tabs.values():
                    group_dict[form] = form.groups()

        return group_dict

    def reset(self, widgets: dict[str, ParameterWidget] | None = None) -> None:
        if widgets is None:
            widgets = self.widgets()

        for widget in widgets.values():
            if isinstance(widget, ParameterWidget):
                widget.set_value(widget.default())
            elif isinstance(widget, dict):
                self.reset(widget)

    def set_state(self, state: dict) -> None:
        values = {'expanded_boxes': []}
        values.update(state)
        expanded_boxes = values['expanded_boxes']
        self._set_expanded_boxes(expanded_boxes)

    def set_values(
        self,
        values: dict,
        widgets: dict[str, ParameterWidget] | None = None,
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
                try:
                    setter = getattr(widget, f'set_{attr}')
                except AttributeError:
                    continue
                setter(value)

    def state(self) -> dict:
        expanded_boxes = self._expanded_boxes()
        state = {'expanded_boxes': expanded_boxes}
        return state

    def values(self) -> dict[str, typing.Any]:
        # create nested dictionary of all Parameter values
        values = {}
        for name, widget in self._widgets.items():
            if isinstance(widget, ParameterForm):
                if widget.create_hierarchy:
                    values[name] = widget.values()
                else:
                    values.update(widget.values())
            else:
                values[name] = widget.value()
        return values

    def widgets(self) -> dict[str, ParameterWidget]:
        # create nested dictionary of all Parameter widgets
        widgets = {}
        for name, widget in self._widgets.items():
            if isinstance(widget, ParameterForm):
                if widget.create_hierarchy:
                    widgets[name] = widget.widgets()
                else:
                    widgets.update(widget.widgets())
            else:
                widgets[name] = widget
        return widgets

    def _expanded_boxes(self, groups: dict | None = None) -> list[str]:
        # returns a list of all expanded boxes
        # child boxes are separated by / 'parent/child/grand-child'
        if groups is None:
            groups = self.groups()

        expanded_boxes = []
        for group, children in groups.items():
            if isinstance(group, ParameterBox):
                title = group.title()
                if not group.collapsed():
                    expanded_boxes.append(group.title())
            elif isinstance(group, ParameterForm):
                title = group.name
            else:
                continue

            child_boxes = self._expanded_boxes(children)
            child_boxes = ['/'.join([title, child]) for child in child_boxes]
            expanded_boxes.extend(child_boxes)
        return expanded_boxes

    def _create_form(self, name) -> ParameterForm:
        self._validate_name(name)

        form = ParameterForm(name=name, root=self)
        self._widgets[name] = form

        return form

    def _hierarchical_names(self) -> list[str]:
        # generate a flat list of all child widget names
        names = []
        for name, widget in self._widgets.items():
            if isinstance(widget, ParameterForm):
                names.extend(widget.hierarchical_names())
            else:
                names.append(name)
        return names

    def _set_expanded_boxes(
        self, expanded_boxes: list[str], groups: dict | None = None
    ) -> None:
        # collapses the boxes in the list, child boxes are separated by dot 'parent.child'

        if groups is None:
            groups = self.groups()

        for group, children in groups.items():
            if isinstance(group, ParameterBox):
                group.set_collapsed(group.title() not in expanded_boxes)
                title = group.title()
            elif isinstance(group, ParameterForm):
                title = group.name
            else:
                continue

            child_boxes = [
                b.split('.', 1)[-1]
                for b in expanded_boxes
                if b.split('/', 1)[0] == title
            ]
            self._set_expanded_boxes(child_boxes, children)

    # noinspection PyMethodMayBeStatic
    def _set_widget_row_enabled(self, widget: QtWidgets.QWidget, enabled: bool) -> None:
        # get parent grid layout
        layout = widget.parentWidget().layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            return

        # find row of widget
        index = layout.indexOf(widget)
        if index < 0:
            return
        row, column, row_span, col_span = layout.getItemPosition(index)

        # widget
        item = layout.itemAtPosition(row, 2)
        if not item or not item.widget():
            return

        item_widget = item.widget()
        item_widget.setEnabled(enabled)

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


class ParameterEditor(ParameterForm):
    def __init__(
        self,
        name: str | None = None,
        root: ParameterEditor | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(name, root, parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        scroll_area = VerticalScrollArea(self)
        self.layout().addWidget(scroll_area)
        self.layout().setContentsMargins(QtCore.QMargins())

        self._form_widget = QtWidgets.QWidget(self)
        self._form_widget.setLayout(QtWidgets.QGridLayout())
        scroll_area.setWidget(self._form_widget)

    @property
    def grid_layout(self) -> QtWidgets.QGridLayout:
        layout = self._form_widget.layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise RuntimeError('Layout needs to be QGridLayout')
        return layout


__all__ = ['ParameterEditor', 'ParameterBox', 'ParameterForm', 'ParameterTabWidget']
