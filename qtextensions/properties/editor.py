import enum
import itertools
import json
from functools import partial
import logging
from typing import Any

from PySide2 import QtWidgets, QtCore, QtGui

# TODO: widgets is a shit name cause i use that name a lot
from qtproperties import utils, widgets
from qtproperties.group import CollapsibleBox


# TODO: initialize widget with updated min_size_hint?
class VerticalScrollArea(QtWidgets.QScrollArea):
    # ScrollArea widget that has a minimum width based on its content

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def eventFilter(self, watched, event):
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

    def update(self):
        min_width = self.widget().minimumSizeHint().width()
        self.setMinimumWidth(min_width)

    def sizeHint(self):
        widget = self.widget() or self
        return widget.sizeHint()


class PropertyEditor(VerticalScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        # set 'form' attribute on this class
        self.__dict__['form'] = PropertyForm()
        self.setWidget(self.form)

    def __getattr__(self, item):
        return getattr(self.form, item)

    def __setattr__(self, key, value):
        setattr(self.form, key, value)


class PropertyForm(QtWidgets.QWidget):
    actions_changed = QtCore.Signal(list)
    property_changed = QtCore.Signal(widgets.PropertyWidget)

    def __init__(self, name=None, root=None, parent=None):
        super().__init__(parent)

        # require unique names in the whole hierarchy
        self.unique_hierarchical_names = False
        # when querying widgets or values, should these values be in their own hierarchy
        self.create_hierarchy = True

        self._widgets = {}
        self.root = root or self
        self.name = name

        # init ui
        self.setLayout(QtWidgets.QGridLayout(self))

    def __repr__(self):
        return f'{self.__class__.__name__}(\'{self.name}\')'

    def actionEvent(self, event: QtGui.QActionEvent) -> None:
        super().actionEvent(event)
        self.actions_changed.emit(self.actions())

    def validate_name(self, name):
        if name is None:
            raise ValueError(f'Cannot add widget with name {name}')

        # check if name is unique relative to root
        if self.root.unique_hierarchical_names:
            hierarchical_names = self.root.hierarchical_names()
        else:
            hierarchical_names = list(self._widgets.keys())
        if name in hierarchical_names:
            raise ValueError(f'Cannot add widget {name} (name already exists)')

    def hierarchical_names(self):
        # generate a flat list of all child widget names
        names = []
        for name, widget in self._widgets.items():
            if isinstance(widget, self.__class__):
                names.extend(widget.hierarchical_names())
            else:
                names.append(name)
        return names

    def create_form(self, name, link=None):
        self.validate_name(name)

        form = PropertyForm(name=name, root=self)
        self._widgets[name] = form

        if link is not None:
            form.link(link)

        return form

    def link(self, link):
        for name, widget in link._widgets.items():
            if isinstance(widget, self.__class__):
                # TODO: add support for linking nested groups
                # this requires to keep track of group type and not just forms
                pass
            else:
                new_widget = widget.copy()
                self.add_property(new_widget, link=widget)

    def add_group(
        self, name, label=None, collapsible=False, style=None, link=None
    ) -> 'PropertyForm':
        form = self.create_form(name, link)
        form.property_changed.connect(self.property_changed.emit)
        label = label or utils.title(name)
        group = CollapsibleBox(label, collapsible, style)

        group.setLayout(QtWidgets.QVBoxLayout(self))
        group.layout().setContentsMargins(0, 0, 0, 0)
        group.layout().setSpacing(0)
        group.layout().addWidget(form)

        # update CollapsibleBox with actions for the menu
        form.actions_changed.connect(group.update_actions)

        self.add_widget(group)
        return form

    def add_tab_group(self, names, labels=None, link=None):
        group = QtWidgets.QTabWidget(self)
        group.tabs = {}
        labels = labels or []
        for name, label in itertools.zip_longest(names, labels):
            form = self.create_form(name, link)
            label = label or utils.title(name)
            group.addTab(form, label)
            group.tabs[name] = form

        self.add_widget(group)
        return group

    def add_property(
        self, widget: widgets.PropertyWidget, link: widgets.PropertyWidget | None = None
    ) -> widgets.PropertyWidget:
        name = widget.name
        self.validate_name(name)

        self._widgets[name] = widget

        layout = self.grid_layout
        row = layout.rowCount() - 1

        # label
        if widget.label:
            label = QtWidgets.QLabel(widget.label, self)
            layout.addWidget(label, row, 1)
            widget.enabledChanged.connect(label.setEnabled)
            widget.enabledChanged.emit(widget.isEnabled())

        # widget
        layout.addWidget(widget, row, 2)
        widget.valueChanged.connect(lambda: self.property_changed.emit(widget))

        # checkbox
        if link is not None:
            widget.link = link
            checkbox = QtWidgets.QCheckBox(self)
            layout.addWidget(checkbox, row, 0)
            checkbox.toggled.connect(partial(self.set_widget_row_enabled, checkbox))
            checkbox.setChecked(False)
            self.set_widget_row_enabled(checkbox, False)

        self.update_stretch()
        return widget

    def add_separator(self):
        line = QtWidgets.QFrame(self)
        line.setFixedHeight(1)
        line.setFrameShape(QtWidgets.QFrame.StyledPanel)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.add_widget(line)
        return line

    def add_widget(self, widget):
        layout = self.grid_layout
        row = layout.rowCount() - 1
        layout.addWidget(widget, row, 0, 1, 3)
        self.update_stretch()
        return widget

    def add_layout(self, layout):
        grid_layout = self.grid_layout
        row = grid_layout.rowCount() - 1
        grid_layout.addLayout(layout, row, 0, 1, 3)
        self.update_stretch()
        return layout

    def update_stretch(self):
        layout = self.grid_layout
        layout.setRowStretch(layout.rowCount() - 1, 0)
        layout.setRowStretch(layout.rowCount(), 1)

    @property
    def grid_layout(self):
        layout = self.layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise RuntimeError('Layout needs to be QGridLayout')
        return layout

    def set_widget_row_enabled(self, widget, enabled):
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
        item = layout.itemAtPosition(row, 2)
        if not item or not item.widget():
            return

        widget = item.widget()
        widget.setEnabled(enabled)

        if hasattr(widget, 'link') and widget.link is not None:
            if not hasattr(widget, 'set_value'):
                widget.set_value = partial(setattr, widget, 'value')
            if enabled:
                widget.link.valueChanged.disconnect(widget.set_value)
            else:
                widget.value = widget.link.value
                widget.link.valueChanged.connect(widget.set_value)

    def update_widget_values(self, values, widgets=None):
        if widgets is None:
            widgets = self.widgets()
        for key, value in values.items():
            if key not in widgets:
                continue
            widget = widgets[key]
            if isinstance(widget, dict):
                self.update_widget_values(value, widget)
            else:
                widget.value = value

    def values(self) -> dict[str, Any]:
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

    def widgets(self) -> dict[str, widgets.PropertyWidget]:
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


def main():
    import sys
    import widgets
    import logging

    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    editor = PropertyEditor()

    editor.add_property(widgets.IntProperty('int'))
    editor.add_property(widgets.FloatProperty('float'))
    editor.add_separator()
    editor.add_property(widgets.PointProperty('point'))
    editor.add_property(widgets.PointFProperty('pointf'))
    editor.add_property(widgets.BoolProperty('bool'))
    editor.add_property(widgets.PathProperty('path'))
    editor.add_property(widgets.StringProperty('string'))
    editor.add_property(widgets.ColorProperty('color'))
    editor.add_property(
        widgets.EnumProperty('enum', enum=enum.Enum('Number', ('one', 'two', 'three')))
    )

    group1 = editor.add_group('group_1', collapsible=True, style=CollapsibleBox.BUTTON)

    group1.add_property(widgets.IntProperty('int'))
    group1.add_property(widgets.FloatProperty('float'))

    group1_menu = editor.add_group(
        'group1_menu', collapsible=True, style=CollapsibleBox.BUTTON
    )
    group1_menu.add_property(widgets.IntProperty('int'))
    group1_menu.add_property(widgets.FloatProperty('float'))

    action = QtWidgets.QAction('Save', group1_menu)
    group1_menu.addAction(action)
    group1_menu.addAction(QtWidgets.QAction('Save1', group1_menu))
    group1_menu.addAction(QtWidgets.QAction('Save2', group1_menu))

    group2 = editor.add_group('group_2', collapsible=False, style=CollapsibleBox.SIMPLE)

    group2.add_property(widgets.IntProperty('int'))
    group2.add_property(widgets.FloatProperty('float'))

    group1_nested = group2.add_group(
        'group_1_nested', collapsible=True, style=CollapsibleBox.BUTTON
    )
    group1_nested.add_property(widgets.IntProperty('int'))
    group1_nested.add_property(widgets.FloatProperty('float'))

    editor.add_property(widgets.IntProperty('int3'))
    editor.add_property(widgets.FloatProperty('float3'))

    group3 = editor.add_tab_group(('tab_1', 'tab_2'))

    group3.tabs['tab_1'].add_property(widgets.IntProperty('int4'))
    group3.tabs['tab_1'].add_property(widgets.FloatProperty('float4'))

    group4 = editor.add_group('group_4', collapsible=True, style=CollapsibleBox.SIMPLE)

    group4.add_property(widgets.IntProperty('int'))
    group4.add_property(widgets.FloatProperty('float'))

    group4_menu = editor.add_group(
        'group_4_menu', collapsible=True, style=CollapsibleBox.SIMPLE
    )

    group4_menu.add_property(widgets.IntProperty('int'))
    group4_menu.add_property(widgets.FloatProperty('float'))

    group4_menu.addAction(QtWidgets.QAction('Save', group4_menu))
    group4_menu.addAction(QtWidgets.QAction('Save1', group4_menu))
    group4_menu.addAction(QtWidgets.QAction('Save2', group4_menu))

    editor.add_property(widgets.StringProperty('text', area=True))

    # editor.values_changed.connect(logging.debug)
    # logging.debug(json.dumps(editor.values(), indent=4, default=lambda x: str(x)))
    editor.property_changed.connect(logging.debug)

    editor.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
