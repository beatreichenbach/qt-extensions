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

    @property
    def fields(self) -> list[Field]:
        return self._fields

    @fields.setter
    def fields(self, value: list[Field]) -> None:
        # TODO: regenerate items based on data
        self._fields = value
        self.refresh_header_labels()

    def dropMimeData(
        self,
        data: QtCore.QMimeData,
        action: QtCore.Qt.DropAction,
        row: int,
        column: int,
        parent: QtCore.QModelIndex,
    ) -> bool:
        if action == QtCore.Qt.MoveAction:
            self._index_move(parent)
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
        parent_item = None
        if parent is not None and parent.isValid():
            parent_item = self.itemFromIndex(parent)
            if parent_item and check_flag(parent_item, QtCore.Qt.ItemNeverHasChildren):
                parent_item = parent_item.parent()

        if parent_item is None:
            parent_item = self.invisibleRootItem()

        items = self._create_items(data, icon, movable, no_children)
        parent_item.appendRow(items)

        self.element_added.emit(data)

    def data_value(self, data: Any, field: Field):
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

    def index_from_value(
        self,
        value: Any,
        field: Field | None = None,
        parent: QtCore.QModelIndex | None = None,
    ):
        if parent is None or value is None:
            parent = QtCore.QModelIndex()

        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if not index.isValid():
                continue

            data = index.data(QtCore.Qt.UserRole)
            if field is None:
                match = data == value
            else:
                match = self.data_value(data, field) == value

            if match:
                return index

    def refresh_header_labels(self) -> None:
        labels = [field.label for field in self.fields]
        super().setHorizontalHeaderLabels(labels)

    def _create_items(
        self, data, icon, movable, no_children
    ) -> list[QtGui.QStandardItem]:
        items = []

        for field in self.fields:
            value = self.data_value(data, field)
            text = '' if value is None else str(value)
            item = QtGui.QStandardItem(text)

            if field.editable and movable:
                item.setData(value, QtCore.Qt.EditRole)
            else:
                item.setEditable(False)

            item.setDragEnabled(movable)
            item.setDropEnabled(not no_children)
            set_flag(item, QtCore.Qt.ItemNeverHasChildren, no_children)

            items.append(item)

        if items:
            item = items[0]
            item.setData(data, QtCore.Qt.UserRole)
            if icon:
                item.setIcon(icon)

        return items

    def _index_move(self, parent: QtCore.QModelIndex) -> None:
        if parent.isValid() and not check_flag(parent, QtCore.Qt.ItemIsDropEnabled):
            return

        if self.selected_indexes:
            for index in self.selected_indexes:
                data = index.data(QtCore.Qt.UserRole)
                self.element_moved.emit(data, parent)
            self.selected_indexes = []


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
    selected_elements_changed: QtCore.Signal = QtCore.Signal(list)

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
        # if class_groups then don't allow drag onto items with different data classes
        if self.class_groups:
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
        self._update_selected_indexes()
        elements = [index.data(QtCore.Qt.UserRole) for index in self.selected_indexes]
        self.selected_elements_changed.emit(elements)
        super().selectionChanged(selected, deselected)

    def _update_selected_indexes(self) -> None:
        # used for tracking elements about to be moved
        indexes = []
        model = self.model()
        if model:
            indexes = self.selectionModel().selectedRows()
            if model.sourceModel():
                indexes = [model.mapToSource(index) for index in indexes]
                model = model.sourceModel()
            model.selected_indexes = indexes
        self.selected_indexes = indexes


class ElementBrowser(QtWidgets.QWidget):
    selected_elements_changed: QtCore.Signal = QtCore.Signal(list)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._init_model()
        self._init_ui()

    def _init_model(self):
        self.model = ElementModel(parent=self)
        self.proxy = ElementProxyModel(parent=self)
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
        self.tree.selected_elements_changed.connect(self.selected_elements_changed.emit)
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

        # if self.unique_names:
        #     element.name = self.model.unique_name(element.name, parent)

        self.model.append_element(data, no_children=True, parent=parent)

    def add_group(self, data: Any = None):
        if data is None:
            data = 'New Group'

        parent = self._selected_index()

        # if self.unique_names:
        #     element.name = self.model.unique_name(element.name, parent)

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
            self.model.append_element(data, icon, movable, no_children, parent)

    def elements(self, parent: QtCore.QModelIndex | None = None) -> list:
        if parent is None:
            parent = QtCore.QModelIndex()
        elements = []
        for row in range(self.model.rowCount(parent)):
            index = self.model.index(row, 0, parent)
            if index.isValid():
                data = index.data(QtCore.Qt.UserRole)
                if data is not None:
                    elements.append(data)
            elements.extend(self.elements(index))
        return elements

    def update_element(self, data: Any):
        index = self.model.index_from_value(data)
        if not index.isValid():
            return

        for i, field in enumerate(self.model.fields):
            value = self.model.data_value(data, field)
            text = '' if value is None else str(value)
            item_index = index.siblingAtColumn(i)
            if item_index.isValid():
                self.model.setData(item_index, text, QtCore.Qt.DisplayRole)

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

    def _selected_index(self) -> QtCore.QModelIndex:
        indexes = self.tree.selectionModel().selectedRows()
        if indexes:
            index = self.proxy.mapToSource(indexes[0])
        else:
            index = QtCore.QModelIndex()
        return index


def main():
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    widget = ElementBrowser()
    widget.model.fields = [Field(name='name', editable=True)]
    widget.tree.setHeaderHidden(True)
    widget.model.element_added.connect(lambda data: logging.info(data))
    widget.model.element_removed.connect(lambda data: logging.info(data))
    widget.model.element_changed.connect(
        lambda data, data2: logging.info([data, data2])
    )
    widget.model.element_moved.connect(
        lambda data, parent: logging.info([data, parent])
    )

    data = 100

    widget.add_element(data)
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
