import copy
import dataclasses
import logging
import sys

from typing import Any, Callable

from PySide2 import QtGui, QtCore, QtWidgets

from qt_extensions.helper import title
from qt_extensions.icons import MaterialIcon


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
        self, fields: list[Field] | None = None, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        # # this is used to track elements about to be moved
        self.selected_indexes = []

        if not fields:
            fields = [Field('name')]
        self.fields = fields
        self.refresh_header()

    def clear(self):
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
        element_index = index.siblingAtColumn(0)
        previous = copy.deepcopy(index.data(QtCore.Qt.UserRole))

        result = super().setData(index, value, role)
        if element_index.isValid():
            current = index.data(QtCore.Qt.UserRole)
            self.element_changed.emit(current, previous)
        return result

    def append_element(
        self,
        element: Any = None,
        icon: QtGui.QIcon | None = None,
        movable: bool = True,
        no_children: bool = False,
        parent: QtCore.QModelIndex | None = None,
    ) -> None:
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

    def element(self, index: QtCore.QModelIndex):
        data = index.siblingAtColumn(0).data(QtCore.Qt.UserRole)
        return data

    def elements(self, parent: QtCore.QModelIndex | None = None) -> list:
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
        return elements

    def find_index(
        self,
        value: Any,
        field: Field | None = None,
        parent: QtCore.QModelIndex | None = None,
    ) -> QtCore.QModelIndex:
        # TODO: find index is not guaranteed to return the correct index if multiple elements are equal
        if parent is None or value is None:
            parent = QtCore.QModelIndex()

        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if not index.isValid():  # optimization
                continue

            data = index.data(QtCore.Qt.UserRole)
            if field is None and value == data:
                return index
            elif value == self._value(data, field):
                return index

            index = self.find_index(value, field, index)
            if index.isValid():
                return index
        return QtCore.QModelIndex()

    def refresh_element(self, element: Any) -> None:
        # update the DisplayRole based on the element stored in the first item
        index = self.find_index(element)
        if not index.isValid():
            return

        for column, field in enumerate(self.fields):
            item_index = index.siblingAtColumn(column)
            value = self._value(element, field)
            self.setData(item_index, value, QtCore.Qt.DisplayRole)

    def refresh_header(self) -> None:
        labels = [field.label for field in self.fields]
        self.setHorizontalHeaderLabels(labels)

    def _value(self, element: Any, field: Field):
        if isinstance(element, (str, int, float)):
            value = element
        elif isinstance(element, dict):
            value = element.get(field.name)
        elif isinstance(element, (list, tuple)):
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


class ElementProxyModel(QtCore.QSortFilterProxyModel):
    # autoAcceptChildRows is a Qt6 feature
    _autoAcceptChildRows = False

    def autoAcceptChildRows(self) -> bool:
        return self._autoAcceptChildRows

    def setAutoAcceptChildRows(self, value: bool):
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

    def selected_elements(self):
        elements = [index.data(QtCore.Qt.UserRole) for index in self.selected_indexes]
        return elements

    def resize_columns(self) -> None:
        if self.model():
            self.expandAll()
            for column in range(self.model().columnCount()):
                self.resizeColumnToContents(column)
            self.collapseAll()


class ElementBrowser(QtWidgets.QWidget):
    selection_changed: QtCore.Signal = QtCore.Signal()

    def __init__(
        self, fields: list[Field] | None = None, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._fields = fields
        self._actions = {}

        self._init_model()
        self._init_ui()

    def _init_model(self):
        self.model = ElementModel(self._fields, self)
        self.proxy = ElementProxyModel(self)
        self.proxy.setAutoAcceptChildRows(True)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setRecursiveFilteringEnabled(True)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSourceModel(self.model)

    def _init_ui(self):
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

    def add_element(self):
        element = 'New Element'
        parent = self._current_parent()
        self.model.append_element(element, no_children=True, parent=parent)

    def add_group(self):
        element = 'New Group'
        parent = self._current_parent()
        self.model.append_element(element, icon=MaterialIcon('folder'), parent=parent)

    def add_toolbar_action(
        self,
        name: str,
        label: str | None = None,
        icon: QtGui.QIcon | None = None,
        slot: Callable | None = None,
    ):
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

    def duplicate_selected(self) -> None:
        for index in self.tree.selected_indexes:
            element = index.data(QtCore.Qt.UserRole)
            element = copy.deepcopy(element)
            icon = index.data(QtCore.Qt.DecorationRole)
            movable = check_flag(index, QtCore.Qt.ItemIsDragEnabled)
            no_children = check_flag(index, QtCore.Qt.ItemNeverHasChildren)
            parent = index.parent()
            self.model.append_element(element, icon, movable, no_children, parent)

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

    def selected_elements(self) -> list:
        return self.tree.selected_elements()

    def _current_parent(self):
        indexes = self.tree.selected_indexes
        if indexes:
            index = indexes[0]
            if check_flag(index, QtCore.Qt.ItemNeverHasChildren):
                index = index.parent()
        else:
            index = QtCore.QModelIndex()
        return index

    def _update_action_states(self):
        indexes = self.tree.selected_indexes
        no_children = False
        movable = True
        if indexes:
            no_children = check_flag(indexes[0], QtCore.Qt.ItemNeverHasChildren)
            movable = check_flag(indexes[0], QtCore.Qt.ItemIsDragEnabled)

        self._actions['remove'].setEnabled(bool(indexes) and movable)
        self._actions['duplicate_element'].setEnabled(bool(indexes) and no_children)


class Foo:
    pass


def main():
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    widget = ElementBrowser([Field('name'), Field('focal')])
    # widget.model.element_added.connect(lambda data: logging.info(data))
    # widget.model.element_removed.connect(lambda data: logging.info(data))
    # widget.model.element_changed.connect(
    #     lambda data, data2: logging.info([data, data2])
    # )
    # widget.model.element_moved.connect(
    #     lambda data, parent: logging.info([data, parent])
    # )

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
