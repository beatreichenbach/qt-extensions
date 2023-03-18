import copy
import dataclasses
import logging
import sys

from typing import Any

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

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        # # this is used to track elements about to be moved
        self.selected_indexes = []

        self._fields = []
        self.fields = []  # set defaults

    @property
    def fields(self) -> list[Field]:
        return self._fields

    @fields.setter
    def fields(self, value: list[Field]) -> None:
        if not value:
            value = [Field('name', editable=False)]
        self._fields = value
        self.refresh_header()

    def dropMimeData(
        self,
        data: QtCore.QMimeData,
        action: QtCore.Qt.DropAction,
        row: int,
        column: int,
        parent: QtCore.QModelIndex,
    ) -> bool:
        if action == QtCore.Qt.MoveAction:
            if self.selected_indexes:
                for index in self.selected_indexes:
                    element = index.data(QtCore.Qt.UserRole)
                    self.element_moved.emit(element, parent)
                self.selected_indexes = []
        return super().dropMimeData(data, action, row, 0, parent.siblingAtColumn(0))

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
        data: Any = None,
        icon: QtGui.QIcon | None = None,
        movable: bool = True,
        no_children: bool = False,
        parent: QtCore.QModelIndex | None = None,
    ) -> None:
        # get parent QStandardItem
        parent_item = None
        if parent is not None and parent.isValid():
            parent_item = self.itemFromIndex(parent)
            if parent_item and check_flag(parent_item, QtCore.Qt.ItemNeverHasChildren):
                parent_item = parent_item.parent()

        if parent_item is None:
            parent_item = self.invisibleRootItem()

        # create QStandardItems
        items = []
        for field in self.fields:
            value = self._data_value(data, field)
            item = QtGui.QStandardItem(value)
            item.setEditable(field.editable and movable)
            item.setDragEnabled(movable)
            item.setDropEnabled(not no_children)
            set_flag(item, QtCore.Qt.ItemNeverHasChildren, no_children)
            items.append(item)

        # update QStandardItems
        if items:
            item = items[0]
            item.setData(data, QtCore.Qt.UserRole)
            if icon:
                item.setIcon(icon)
            parent_item.appendRow(items)
            self.element_added.emit(data)

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

    def refresh_element(self, data: Any) -> None:
        # update the DisplayRole based on the data stored in the first item
        index = self._index_from_element(data)
        if not index.isValid():
            return

        for column, field in enumerate(self.fields):
            item_index = index.siblingAtColumn(column)
            value = self._data_value(data, field)
            self.setData(item_index, value, QtCore.Qt.DisplayRole)

    def refresh_header(self) -> None:
        labels = [field.label for field in self.fields]
        self.setHorizontalHeaderLabels(labels)

    def _data_value(self, data: Any, field: Field):
        if isinstance(data, (str, int, float)):
            value = data
        elif isinstance(data, dict):
            value = data.get(field.name)
        elif isinstance(data, (list, tuple)):
            try:
                i = self.fields.index(field)
                value = data[i]
            except (KeyError, ValueError):
                value = None
        else:
            try:
                value = getattr(data, field.name)
            except AttributeError:
                value = None
        return value

    def _index_from_element(
        self,
        data: Any,
        parent: QtCore.QModelIndex | None = None,
    ) -> QtCore.QModelIndex:
        if parent is None:
            parent = QtCore.QModelIndex()

        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if not index.isValid():  # optimization
                continue

            if index.data(QtCore.Qt.UserRole) == data:
                return index

            index = self._index_from_element(data, index)
            if index.isValid():
                return index

        return QtCore.QModelIndex()


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

        if is_left_group != is_right_group:
            return False
        else:
            result = super().lessThan(source_left, source_right)
            return result


class ElementDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        if not check_flag(index, QtCore.Qt.ItemIsDragEnabled):
            option.font.setBold(True)
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
            # don't allow drag onto items with different data classes
            index = self.indexAt(event.pos())
            parent_data = index.data(QtCore.Qt.UserRole)
            if parent_data is not None:
                for index in self.selected_indexes:
                    data = index.data(QtCore.Qt.UserRole)
                    if not isinstance(data, type(parent_data)):
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


class ElementBrowser(QtWidgets.QWidget):
    selection_changed: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._init_model()
        self._init_ui()

    def _init_model(self):
        self.model = ElementModel(self)
        self.proxy = ElementProxyModel(self)
        self.proxy.setAutoAcceptChildRows(True)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setRecursiveFilteringEnabled(True)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSourceModel(self.model)

    def _init_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())

        self.toolbar = QtWidgets.QToolBar()
        icon_size = self.toolbar.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self.toolbar.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.layout().addWidget(self.toolbar)

        icon = MaterialIcon('add')
        action = QtWidgets.QAction(icon, 'Add Element', self)
        action.triggered.connect(lambda: self.add_element())
        self.toolbar.addAction(action)

        icon = MaterialIcon('remove')
        action = QtWidgets.QAction(icon, 'Remove Element', self)
        action.triggered.connect(self.remove_selected_elements)
        self.toolbar.addAction(action)

        icon = MaterialIcon('content_copy')
        action = QtWidgets.QAction(icon, 'Duplicate', self)
        action.triggered.connect(lambda: self.duplicate_element())
        self.toolbar.addAction(action)

        icon = MaterialIcon('create_new_folder')
        action = QtWidgets.QAction(icon, 'Add Group', self)
        action.triggered.connect(lambda: self.add_group())
        self.toolbar.addAction(action)

        filter_bar = QtWidgets.QLineEdit()
        filter_bar.setPlaceholderText('Filter...')
        filter_bar.textChanged.connect(self.filter)
        action = self.toolbar.addWidget(filter_bar)
        action.setText('Filter')

        self.tree = ElementTree()
        self.tree.setModel(self.proxy)
        self.tree.selection_changed.connect(self.selection_changed.emit)
        self.layout().addWidget(self.tree)

    def filter(self, text: str) -> None:
        self.tree.collapseAll()
        self.proxy.setFilterWildcard(text)
        if text:
            self.tree.expandAll()

    def add_element(self, data: Any = None):
        if data is None:
            data = 'New Element'

        parent = self._selected_index()
        self.model.append_element(data, no_children=True, parent=parent)

    def add_group(self, data: Any = None):
        if data is None:
            data = 'New Group'

        parent = self._selected_index()
        self.model.append_element(data, icon=MaterialIcon('folder'), parent=parent)

    def duplicate_element(self):
        for index in self.tree.selected_indexes:
            movable = check_flag(index, QtCore.Qt.ItemIsDragEnabled)
            if not movable:
                continue
            data = index.data(QtCore.Qt.UserRole)
            data = copy.deepcopy(data)
            icon = index.data(QtCore.Qt.DecorationRole)
            no_children = check_flag(index, QtCore.Qt.ItemNeverHasChildren)

            parent = self._selected_index().parent()
            self._append_element(data, icon, movable, no_children, parent)

    def remove_selected_elements(self) -> None:
        indexes = self.tree.selectionModel().selectedRows()

        # build list of persistent indexes so that indexes don't changed
        # as rows are removed
        persistent_indexes = [
            QtCore.QPersistentModelIndex(self.proxy.mapToSource(index))
            for index in indexes
        ]
        for index in persistent_indexes:
            if index.isValid() and check_flag(index, QtCore.Qt.ItemIsDragEnabled):
                self.model.removeRow(index.row(), index.parent())

    def selected_elements(self):
        elements = [
            index.data(QtCore.Qt.UserRole) for index in self.tree.selected_indexes
        ]
        return elements

    def _selected_index(self) -> QtCore.QModelIndex:
        indexes = self.tree.selectionModel().selectedRows()
        if indexes:
            index = self.proxy.mapToSource(indexes[0])
        else:
            index = QtCore.QModelIndex()
        return index


class Foo:
    pass


def main():
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    widget = ElementBrowser()
    widget.tree.setHeaderHidden(True)
    # widget.model.element_added.connect(lambda data: logging.info(data))
    # widget.model.element_removed.connect(lambda data: logging.info(data))
    # widget.model.element_changed.connect(
    #     lambda data, data2: logging.info([data, data2])
    # )
    # widget.model.element_moved.connect(
    #     lambda data, parent: logging.info([data, parent])
    # )

    data = Foo()
    data.name = 'Bob'
    # data = 'Bob'

    widget.add_element(data)

    widget.model.fields = [Field('name'), Field('focal')]

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
