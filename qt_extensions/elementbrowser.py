from __future__ import annotations

import copy
import dataclasses
from collections.abc import Sequence
from typing import Any, Callable

from PySide2 import QtGui, QtCore, QtWidgets
from qt_material_icons import MaterialIcon

from qt_extensions.helper import title


def set_flag(item: QtGui.QStandardItem, flag: QtCore.Qt.ItemFlag, value: bool) -> None:
    if value:
        item.setFlags(item.flags() | flag)
    else:
        item.setFlags(item.flags() & ~flag)


def check_flag(
    item: QtGui.QStandardItem | QtCore.QModelIndex, flag: QtCore.Qt.ItemFlag
) -> bool:
    return bool(item.flags() & flag)


@dataclasses.dataclass
class Field:
    name: str = ''
    label: str | None = None
    editable: bool = False

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = title(self.name)


class ElementModel(QtGui.QStandardItemModel):
    element_added: QtCore.Signal = QtCore.Signal(object)
    element_changed: QtCore.Signal = QtCore.Signal(object, object)
    element_moved: QtCore.Signal = QtCore.Signal(object, QtCore.QModelIndex)
    element_removed: QtCore.Signal = QtCore.Signal(object)

    def __init__(
        self, fields: Sequence[Field] = (), parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        # this is used to track elements about to be moved
        self.selected_indexes = []

        if not fields:
            fields = (Field('name'),)
        self.fields = fields
        self.refresh_header()

    def clear(self) -> None:
        super().clear()
        self.refresh_header()

    def dropMimeData(
        self,
        data: QtCore.QMimeData,
        action: QtCore.Qt.DropAction,
        row: int,
        column: int,
        parent: QtCore.QModelIndex,
    ) -> bool:
        result = super().dropMimeData(data, action, row, 0, parent.siblingAtColumn(0))
        if result and action == QtCore.Qt.MoveAction:
            for index in self.selected_indexes:
                element = index.data(QtCore.Qt.UserRole)
                self.element_moved.emit(element, parent)
            self.selected_indexes = []
        return result

    def removeRow(
        self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        index = self.index(row, 0, parent)
        if index.isValid():
            self.element_removed.emit(index.data(QtCore.Qt.UserRole))
        return super().removeRow(row, parent)

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: Any,
        role: int = QtCore.Qt.EditRole,
    ) -> Any:
        result = super().setData(index, value, role)
        if result and role & QtCore.Qt.DisplayRole | QtCore.Qt.EditRole:
            element_index = index.siblingAtColumn(0)
            if element_index.isValid():
                element = index.data(QtCore.Qt.UserRole)
                previous = copy.deepcopy(element)

                try:
                    field = self.fields[index.column()]
                except KeyError:
                    return False

                element = self._set_value(element, value, field)
                self.element_changed.emit(element, previous)
        return result

    def append_element(
        self,
        element: Any = None,
        icon: QtGui.QIcon | None = None,
        movable: bool = True,
        no_children: bool = False,
        parent: QtCore.QModelIndex | None = None,
    ) -> QtCore.QModelIndex:
        # get parent QStandardItem
        parent_item = self.itemFromIndex(parent) if parent else None
        if parent_item is None:
            parent_item = self.invisibleRootItem()

        # create QStandardItems
        items = []
        for field in self.fields:
            value = self._value(element, field)
            item = QtGui.QStandardItem(value)
            item.setEditable(field.editable and movable)
            item.setDragEnabled(movable)
            item.setDropEnabled(not no_children)
            set_flag(item, QtCore.Qt.ItemNeverHasChildren, no_children)
            items.append(item)

        # update QStandardItems
        if items:
            item = items[0]
            item.setData(element, QtCore.Qt.UserRole)
            if icon:
                item.setIcon(icon)
            parent_item.appendRow(items)
            self.element_added.emit(element)
            return item.index()
        return QtCore.QModelIndex()

    def duplicate_index(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        element = index.data(QtCore.Qt.UserRole)
        copied_element = copy.deepcopy(element)
        icon = index.data(QtCore.Qt.DecorationRole)
        movable = check_flag(index, QtCore.Qt.ItemIsDragEnabled)
        no_children = check_flag(index, QtCore.Qt.ItemNeverHasChildren)
        parent = index.parent()
        copied_index = self.append_element(
            copied_element, icon, movable, no_children, parent
        )
        return copied_index

    def element(self, index: QtCore.QModelIndex) -> Any:
        data = self.data(index.siblingAtColumn(0), QtCore.Qt.UserRole)
        return data

    def elements(self, parent: QtCore.QModelIndex | None = None) -> tuple:
        if parent is None:
            parent = QtCore.QModelIndex()
        elements = []
        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if not index.isValid():  # optimization
                continue
            data = index.data(QtCore.Qt.UserRole)
            if data is not None:
                elements.append(data)
            elements.extend(self.elements(index))
        return tuple(elements)

    def find_indexes(
        self,
        value: Any,
        field: Field | None = None,
        parent: QtCore.QModelIndex | None = None,
    ) -> tuple[QtCore.QModelIndex, ...]:
        indexes = []

        if parent is None or value is None:
            parent = QtCore.QModelIndex()

        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if not index.isValid():  # optimization
                continue

            data = index.data(QtCore.Qt.UserRole)
            if field is None and value == data:
                indexes.append(index)
            elif value == self._value(data, field):
                indexes.append(index)

            indexes.extend(self.find_indexes(value, field, index))
        return tuple(indexes)

    def refresh_index(self, index: QtCore.QModelIndex) -> None:
        element = self.element(index)
        for column, field in enumerate(self.fields):
            item_index = index.siblingAtColumn(column)
            value = self._value(element, field)
            self.setData(item_index, value, QtCore.Qt.DisplayRole)
        # refresh child indexes
        # for row in range(self.rowCount(index)):
        #     self.refresh_index(self.index(row, 0, index))

    def refresh_element(self, element: Any) -> None:
        # update the DisplayRole based on the element stored in the first item
        for index in self.find_indexes(element):
            self.refresh_index(index)

    def refresh_header(self) -> None:
        labels = [field.label for field in self.fields]
        self.setHorizontalHeaderLabels(labels)

    def _value(self, element: Any, field: Field) -> Any:
        if isinstance(element, (str, int, float)):
            value = element
        elif isinstance(element, dict):
            value = element.get(field.name)
        elif isinstance(element, Sequence):
            try:
                i = self.fields.index(field)
                value = element[i]
            except (KeyError, ValueError):
                value = None
        else:
            try:
                value = getattr(element, field.name)
            except AttributeError:
                value = None
        return value

    def _set_value(self, element: Any, value: Any, field: Field) -> Any:
        # the reason for returning element is in case element is an immutable object
        if isinstance(element, (str, int, float)):
            element = value
        elif isinstance(element, dict):
            element[field.name] = value
        elif isinstance(element, Sequence):
            if isinstance(element, tuple):
                element = list(element)
            try:
                i = self.fields.index(field)
                element[i] = value
            except (KeyError, ValueError):
                pass
        else:
            try:
                setattr(element, field.name, value)
            except AttributeError:
                pass
        return element


class ElementProxyModel(QtCore.QSortFilterProxyModel):
    # autoAcceptChildRows is a Qt6 feature
    _autoAcceptChildRows = False

    def autoAcceptChildRows(self) -> bool:  # noqa
        return self._autoAcceptChildRows

    def setAutoAcceptChildRows(self, value: bool):  # noqa
        self._autoAcceptChildRows = value

    def filterAcceptsRow(
        self, source_row: int, source_parent: QtCore.QModelIndex
    ) -> bool:
        if super().filterAcceptsRow(source_row, source_parent):
            return True
        if self.autoAcceptChildRows() and source_parent.isValid():
            source_row = source_parent.row()
            source_parent = source_parent.parent()
            return self.filterAcceptsRow(source_row, source_parent)
        return False

    def lessThan(
        self, source_left: QtCore.QModelIndex, source_right: QtCore.QModelIndex
    ) -> bool:
        # sort elements and groups separately
        is_left_group = check_flag(source_left, QtCore.Qt.ItemNeverHasChildren)
        is_right_group = check_flag(source_right, QtCore.Qt.ItemNeverHasChildren)

        if is_left_group == is_right_group:
            result = super().lessThan(source_left, source_right)
            return result
        else:
            return is_right_group


class ElementDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        if not check_flag(index, QtCore.Qt.ItemIsDragEnabled):
            option.font.setBold(True)
        option.state &= ~QtWidgets.QStyle.State_HasFocus
        super().paint(painter, option, index)

    def sizeHint(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> QtCore.QSize:
        size_hint = super().sizeHint(option, index)
        size_hint = size_hint.grownBy(QtCore.QMargins(0, 4, 0, 4))
        return size_hint


class ElementTree(QtWidgets.QTreeView):
    selection_changed: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.class_groups = True
        self.selected_indexes = []

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setSortingEnabled(True)
        self.setAutoExpandDelay(500)
        self.setItemDelegate(ElementDelegate())

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if self.class_groups:
            # don't allow drag onto items with different element classes
            index = self.indexAt(event.pos())
            parent_element = index.data(QtCore.Qt.UserRole)
            if parent_element is not None:
                for index in self.selected_indexes:
                    element = index.data(QtCore.Qt.UserRole)
                    if not isinstance(element, type(parent_element)):
                        event.ignore()
                        return

        super().dragMoveEvent(event)

    def selectionChanged(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        # store selected indexes
        indexes = []
        model = self.model()
        if model:
            indexes = self.selectionModel().selectedRows()
            if model.sourceModel():
                indexes = [model.mapToSource(index) for index in indexes]
                model = model.sourceModel()

            # used for tracking elements about to be moved
            model.selected_indexes = indexes

        self.selected_indexes = indexes

        self.selection_changed.emit()
        super().selectionChanged(selected, deselected)

    def selected_elements(self) -> tuple:
        elements = (index.data(QtCore.Qt.UserRole) for index in self.selected_indexes)
        return tuple(elements)

    def resize_columns(self) -> None:
        if self.model():
            self.expandAll()
            for column in range(self.model().columnCount()):
                self.resizeColumnToContents(column)
            self.collapseAll()


class ElementBrowser(QtWidgets.QWidget):
    selection_changed: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        fields: Sequence[Field] = (),
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._fields = fields
        self._actions = {}

        self._init_model()
        self._init_ui()

    def _init_model(self) -> None:
        self.model = ElementModel(self._fields, self)
        self.proxy = ElementProxyModel(self)
        self.proxy.setAutoAcceptChildRows(True)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setRecursiveFilteringEnabled(True)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSourceModel(self.model)

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout())

        self.toolbar = QtWidgets.QToolBar()
        icon_size = self.toolbar.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self.toolbar.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.layout().addWidget(self.toolbar)

        self.add_toolbar_action(
            'add_element',
            icon=MaterialIcon('add'),
            slot=self.add_element,
        )
        self.add_toolbar_action(
            'remove',
            icon=MaterialIcon('remove'),
            slot=self.remove_selected,
        )
        self.add_toolbar_action(
            'duplicate_element',
            icon=MaterialIcon('content_copy'),
            slot=self.duplicate_selected,
        )
        self.add_toolbar_action(
            'add_group',
            icon=MaterialIcon('create_new_folder'),
            slot=self.add_group,
        )

        filter_bar = QtWidgets.QLineEdit()
        filter_bar.setPlaceholderText('Filter...')
        filter_bar.textChanged.connect(self.filter)
        action = self.toolbar.addWidget(filter_bar)
        action.setText('Filter')

        self.tree = ElementTree()
        self.tree.setModel(self.proxy)
        self.tree.selection_changed.connect(self.selection_changed.emit)
        self.tree.selection_changed.connect(self._update_action_states)
        if not self._fields:
            self.tree.setHeaderHidden(True)
        self.layout().addWidget(self.tree)

        self._update_action_states()

    def filter(self, text: str) -> None:
        self.tree.collapseAll()
        self.proxy.setFilterWildcard(text)
        if text:
            self.tree.expandAll()

    def add_element(self) -> QtCore.QModelIndex:
        element = 'Unnamed'
        parent = self._current_parent()
        index = self.model.append_element(element, no_children=True, parent=parent)
        return index

    def add_group(self) -> QtCore.QModelIndex:
        element = 'Unnamed'
        parent = self._current_parent()
        index = self.model.append_element(
            element, icon=MaterialIcon('folder'), parent=parent
        )
        return index

    def add_toolbar_action(
        self,
        name: str,
        label: str | None = None,
        icon: QtGui.QIcon | None = None,
        slot: Callable | None = None,
    ) -> QtWidgets.QAction:
        if name in self._actions:
            raise ValueError(f'Action with name {name} already exists.')
        if label is None:
            label = title(name)

        action = QtWidgets.QAction(self)
        if label:
            action.setText(label)
        if icon:
            action.setIcon(icon)
        if slot:
            action.triggered.connect(slot)
        self.toolbar.addAction(action)
        self._actions[name] = action
        return action

    def duplicate_selected(self) -> tuple[QtCore.QModelIndex, ...]:
        indexes = []
        for index in self.tree.selected_indexes:
            copied_index = self.model.duplicate_index(index)
            indexes.append(copied_index)
        return tuple(indexes)

    def elements(self) -> tuple:
        return self.model.elements()

    def remove_toolbar_action(self, name: str) -> None:
        if name in self._actions:
            action = self._actions.pop(name)
            self.toolbar.removeAction(action)

    def remove_selected(self) -> None:
        # build list of persistent indexes so that indexes don't changed
        # as rows are removed
        persistent_indexes = [
            QtCore.QPersistentModelIndex(index) for index in self.tree.selected_indexes
        ]
        for index in persistent_indexes:
            if index.isValid() and check_flag(index, QtCore.Qt.ItemIsDragEnabled):
                self.model.removeRow(index.row(), index.parent())

    def select_elements(self, elements: Sequence) -> None:
        selection_model = self.tree.selectionModel()
        selection_model.clear()
        for element in elements:
            indexes = self.model.find_indexes(element)
            for index in indexes:
                index = self.proxy.mapFromSource(index)
                selection_model.select(index, QtCore.QItemSelectionModel.Select)

    def selected_elements(self) -> tuple:
        return self.tree.selected_elements()

    def _current_parent(self) -> QtCore.QModelIndex:
        indexes = self.tree.selected_indexes
        if indexes:
            index = indexes[0]
            if check_flag(index, QtCore.Qt.ItemNeverHasChildren):
                index = index.parent()
        else:
            index = QtCore.QModelIndex()
        return index

    def _update_action_states(self) -> None:
        indexes = self.tree.selected_indexes
        no_children = False
        movable = True
        if indexes:
            no_children = check_flag(indexes[0], QtCore.Qt.ItemNeverHasChildren)
            movable = check_flag(indexes[0], QtCore.Qt.ItemIsDragEnabled)

        try:
            self._actions['remove'].setEnabled(bool(indexes) and movable)
        except KeyError:
            pass

        try:
            self._actions['duplicate_element'].setEnabled(bool(indexes) and no_children)
        except KeyError:
            pass
