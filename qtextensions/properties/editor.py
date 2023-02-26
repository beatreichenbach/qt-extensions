import dataclasses
import itertools
import logging
from collections.abc import Iterable
from functools import partial
import typing
from typing_extensions import Self

from PySide2 import QtWidgets, QtCore, QtGui

from qtextensions import helper
from qtextensions.scrollarea import VerticalScrollArea
from qtextensions.properties import PropertyWidget
from qtextensions.box import CollapsibleBox
from qtextensions.typeutils import cast


@dataclasses.dataclass()
class BoxState:
    child_states: dict[str, 'BoxState'] = dataclasses.field(default_factory=dict)
    collapsed: bool = True


@dataclasses.dataclass()
class LinkState:
    child_states: dict[str, 'LinkState'] = dataclasses.field(default_factory=dict)
    linked: bool = False


@dataclasses.dataclass()
class EditorState:
    box_states: dict[str, BoxState] = dataclasses.field(default_factory=dict)
    link_states: dict[str, LinkState] = dataclasses.field(default_factory=dict)


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

        self.setLayout(QtWidgets.QGridLayout(self))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)})'

    @property
    def grid_layout(self) -> QtWidgets.QGridLayout:
        layout = self.layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise RuntimeError('Layout needs to be QGridLayout')
        return layout

    @property
    def state(self) -> EditorState:
        box_states = self._box_states()
        link_states = self._link_states()
        state = EditorState(box_states=box_states, link_states=link_states)
        return state

    @state.setter
    def state(self, value: dict) -> None:
        state = cast(EditorState, value)
        self._update_box_states(state.box_states)
        self._update_link_states(state.link_states)

    def actionEvent(self, event: QtGui.QActionEvent) -> None:
        super().actionEvent(event)
        self.actions_changed.emit(self.actions())

    def add_property(
        self, widget: PropertyWidget, link: PropertyWidget | None = None
    ) -> PropertyWidget:
        name = widget.name
        self._validate_name(name)

        self._widgets[name] = widget

        layout = self.grid_layout
        row = layout.rowCount() - 1

        # label
        if widget.label:
            label = QtWidgets.QLabel(widget.label, self)
            layout.addWidget(label, row, 1)
            widget.enabled_changed.connect(label.setEnabled)
            widget.enabled_changed.emit(widget.isEnabled())

        # widget
        layout.addWidget(widget, row, 2)
        widget.value_changed.connect(lambda: self.property_changed.emit(widget))

        # checkbox
        if link is not None:
            widget.link = link
            checkbox = QtWidgets.QCheckBox(self)
            layout.addWidget(checkbox, row, 0)
            checkbox.toggled.connect(partial(self._set_widget_row_enabled, checkbox))
            checkbox.setChecked(False)
            self._set_widget_row_enabled(checkbox, False)

        self._update_stretch()
        return widget

    def add_group(
        self,
        name: str,
        label: str = None,
        collapsible: bool = False,
        style: CollapsibleBox.Style = None,
        link: Self = None,
    ) -> Self:
        form = self._create_form(name, link)
        form.property_changed.connect(self.property_changed.emit)
        label = label or helper.title(name)
        group = CollapsibleBox(label, collapsible, style)
        if collapsible:
            group.collapsed = True

        group.setLayout(QtWidgets.QVBoxLayout(self))
        group.layout().setContentsMargins(0, 0, 0, 0)
        group.layout().setSpacing(0)
        group.layout().addWidget(form)

        # update CollapsibleBox with actions for the menu
        form.actions_changed.connect(group.update_actions)

        self.add_widget(group)
        return form

    def add_tab_group(
        self,
        names: Iterable[str],
        labels: Iterable[str] = None,
        link: Self | None = None,
    ) -> QtWidgets.QTabWidget:
        group = QtWidgets.QTabWidget(self)
        group.tabs = {}
        labels = labels or []
        for name, label in itertools.zip_longest(names, labels):
            form = self._create_form(name, link)
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

    def add_widget(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        layout = self.grid_layout
        row = layout.rowCount() - 1
        layout.addWidget(widget, row, 0, 1, 3)
        self._update_stretch()
        return widget

    def add_layout(self, layout: QtWidgets.QLayout) -> QtWidgets.QLayout:
        grid_layout = self.grid_layout
        row = grid_layout.rowCount() - 1
        grid_layout.addLayout(layout, row, 0, 1, 3)
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

    def update_widget_values(
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
                self.update_widget_values(value, widget)
            elif widget.isEnabled():
                # only set values on enabled widgets, otherwise linked widgets
                # hold the wrong value
                setattr(widget, attr, value)

    @staticmethod
    def _set_widget_row_enabled(widget: QtWidgets.QWidget, enabled: bool) -> None:
        # get parent grid layout
        layout = widget.parentWidget().layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            return

        # find row of widget
        index = layout.indexOf(widget)
        if index < 0:
            return
        row, column, rowspan, colspan = layout.getItemPosition(index)

        # widget
        widgets = list(
            layout.itemAtPosition(row, i).widget() for i in range(layout.columnCount())
        )
        item = layout.itemAtPosition(row, 2)
        if not item or not item.widget():
            return

        item_widget = item.widget()
        item_widget.setEnabled(enabled)

        if (
            isinstance(item_widget, PropertyWidget)
            and hasattr(item_widget, 'link')
            and item_widget.link is not None
        ):
            if not hasattr(item_widget, 'link_set_value'):
                item_widget.link_set_value = partial(setattr, item_widget, 'value')
            if enabled:
                item_widget.link.value_changed.disconnect(item_widget.link_set_value)
            else:
                item_widget.value = item_widget.link.value
                item_widget.link.value_changed.connect(item_widget.link_set_value)

    def _box_states(
        self, boxes: dict[CollapsibleBox, ...] | None = None
    ) -> dict[str, BoxState]:
        # returns the state of all collapsible boxes
        if boxes is None:
            boxes = self.boxes()
        # the collapsed state of all box widgets
        states = {}
        for box, children in boxes.items():
            child_states = self._box_states(children)
            state = BoxState(child_states=child_states, collapsed=box.collapsed)
            states[box.title] = state
        return states

    def _update_box_states(
        self,
        values: dict[str, BoxState],
        boxes: dict[CollapsibleBox, ...] | None = None,
    ) -> None:
        # updates the state of all collapsible boxes
        if boxes is None:
            boxes = self.boxes()
        for box, children in boxes.items():
            state = values.get(box.title)
            if not state:
                continue

            box.collapsed = state.collapsed
            self._update_box_states(state.child_states, children)

    def _link_states(
        self, widgets: dict[str, PropertyWidget] | None = None
    ) -> dict[str, LinkState]:
        if widgets is None:
            widgets = self.widgets()
        # the enabled state of linked widgets
        states = {}
        for key, widget in widgets.items():
            if isinstance(widget, dict):
                child_states = self._link_states(widget)
                if child_states:
                    states[key] = LinkState(child_states=child_states)
            elif hasattr(widget, 'link'):
                linked = not widget.isEnabled()
                states[key] = LinkState(linked=linked)
        return states

    def _update_link_states(
        self,
        values: dict[str, LinkState],
        widgets: dict[str, PropertyWidget] | None = None,
    ) -> None:
        if widgets is None:
            widgets = self.widgets()
        for key, value in values.items():
            widget = widgets.get(key)
            if not widget:
                continue
            if isinstance(value, dict):
                self._update_link_states(values[key].child_states, widget)
            elif hasattr(widget, 'link'):
                # TODO: make safe
                enabled = not value.linked
                PropertyForm._set_widget_row_enabled(widget, enabled)
                # logging.debug((widget.name, widget.link.value))
                # if enabled:
                #     widget.value = widget.link.value

    def _create_form(self, name, link: Self | None = None) -> Self:
        self._validate_name(name)

        form = self.__class__(name=name, root=self)
        self._widgets[name] = form

        if link is not None:
            link = typing.cast('PropertyForm', link)
            form._link(link)

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

    def _link(self, link: Self) -> None:
        for name, widget in link._widgets.items():
            if isinstance(widget, self.__class__):
                # TODO: add support for linking nested groups
                # this requires to keep track of group type and not just forms
                pass
            else:
                new_widget = widget.__class__(widget.name)
                new_widget.init_from(widget)
                self.add_property(new_widget, link=widget)

    def _update_stretch(self) -> None:
        layout = self.grid_layout
        layout.setRowStretch(layout.rowCount() - 1, 0)
        layout.setRowStretch(layout.rowCount(), 1)


def main():
    import sys
    import logging

    from qtextensions import theme
    from qtextensions import properties

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.modern_dark)

    editor = PropertyEditor()

    editor.add_property(properties.IntProperty('int'))
    editor.add_property(properties.FloatProperty('float'))
    editor.add_separator()
    editor.add_property(properties.PointProperty('point'))
    editor.add_property(properties.PointFProperty('pointf'))
    editor.add_property(properties.BoolProperty('bool'))
    editor.add_property(properties.PathProperty('path'))
    editor.add_property(properties.StringProperty('string'))
    editor.add_property(properties.ColorProperty('color'))
    # editor.add_property(
    #     properties.EnumProperty('enum', enum=enum.Enum('Number', ('one', 'two', 'three')))
    # )

    group1 = editor.add_group(
        'group_1', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )

    group1.add_property(properties.IntProperty('int'))
    group1.add_property(properties.FloatProperty('float'))

    group1_menu = editor.add_group(
        'group1_menu', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )
    group1_menu.add_property(properties.IntProperty('int'))
    group1_menu.add_property(properties.FloatProperty('float'))

    action = QtWidgets.QAction('Save', group1_menu)
    group1_menu.addAction(action)
    group1_menu.addAction(QtWidgets.QAction('Save1', group1_menu))
    group1_menu.addAction(QtWidgets.QAction('Save2', group1_menu))

    group2 = editor.add_group(
        'group_2', collapsible=False, style=CollapsibleBox.Style.SIMPLE
    )

    group2.add_property(properties.IntProperty('int'))
    group2.add_property(properties.FloatProperty('float'))

    group1_nested = group2.add_group(
        'group_1_nested', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )
    group1_nested.add_property(properties.IntProperty('int'))
    group1_nested.add_property(properties.FloatProperty('float'))

    editor.add_property(properties.IntProperty('int3'))
    editor.add_property(properties.FloatProperty('float3'))

    group3 = editor.add_tab_group(('tab_1', 'tab_2'))

    group3.tabs['tab_1'].add_property(properties.IntProperty('int4'))
    group3.tabs['tab_1'].add_property(properties.FloatProperty('float4'))

    group4 = editor.add_group(
        'group_4', collapsible=True, style=CollapsibleBox.Style.SIMPLE
    )

    group4.add_property(properties.IntProperty('int'))
    group4.add_property(properties.FloatProperty('float'))

    group4_menu = editor.add_group(
        'group_4_menu', collapsible=True, style=CollapsibleBox.Style.SIMPLE
    )

    group4_menu.add_property(properties.IntProperty('int'))
    group4_menu.add_property(properties.FloatProperty('float'))

    group4_menu.addAction(QtWidgets.QAction('Save', group4_menu))
    group4_menu.addAction(QtWidgets.QAction('Save1', group4_menu))
    group4_menu.addAction(QtWidgets.QAction('Save2', group4_menu))

    prop = properties.StringProperty('text')
    prop.area = True
    editor.add_property(prop)

    # editor.values_changed.connect(logging.debug)
    # logging.debug(json.dumps(editor.values(), indent=4, default=lambda x: str(x)))
    editor.property_changed.connect(logging.debug)

    editor.show()
    state = editor.state()
    editor.update_state(state)

    sys.exit(app.exec_())


__all__ = ['PropertyEditor', 'EditorState']


if __name__ == '__main__':
    main()
