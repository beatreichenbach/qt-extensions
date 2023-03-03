import logging
import os
import dataclasses
import typing
from collections.abc import Iterable

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.icons import MaterialIcon
from qt_extensions.helper import unique_name


@dataclasses.dataclass
class Field:
    name: str = ''
    icon: MaterialIcon = None
    editable: bool = False


@dataclasses.dataclass
class Element:
    fields: list[Field]
    movable: bool = True
    no_children: bool = False
    path: str = ''


class ElementModel(QtGui.QStandardItemModel):
    element_added: QtCore.Signal = QtCore.Signal(Element)
    element_changed: QtCore.Signal = QtCore.Signal(Element, Element)
    element_moved: QtCore.Signal = QtCore.Signal(Element, Element)
    element_removed: QtCore.Signal = QtCore.Signal(Element)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.header_labels = []
        self._last_parent = None

        # this is used to track elements about to be moved
        self.current_elements = None
        self.rowsInserted.connect(self.rows_insert)

        self.columnsInserted.connect(self.columns_insert)

    def rows_insert(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        self._last_parent = parent

    def columns_insert(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        super().setHorizontalHeaderLabels(self.header_labels)

    def setHorizontalHeaderLabels(self, labels: Iterable[str]) -> None:
        # remember header labels in case data gets reset
        self.header_labels = labels
        self.update_max_columns(len(labels))
        super().setHorizontalHeaderLabels(labels)

    def dropMimeData(
        self,
        data: QtCore.QMimeData,
        action: QtCore.Qt.DropAction,
        row: int,
        column: int,
        parent: QtCore.QModelIndex,
    ) -> bool:
        if action == QtCore.Qt.MoveAction:
            self.element_move(parent)
        return super().dropMimeData(data, action, row, 0, parent.siblingAtColumn(0))

    def element_move(self, parent: QtCore.QModelIndex) -> None:
        if not parent.flags() & QtCore.Qt.ItemIsDropEnabled:
            return
        if self.current_elements:
            parent_path = self.path_from_index(parent)
            for element in self.current_elements:
                segment = os.path.basename(element.path)
                path = os.path.join(parent_path, segment)
                current = dataclasses.replace(element)
                current.path = path
                self.element_moved.emit(current, element)
            self.current_elements = None

    def append_element(
        self, element: Element, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> None:
        if parent and parent.isValid():
            parent_item = self.itemFromIndex(parent)
        else:
            parent_item = self.invisibleRootItem()

        items = self.items_from_element(element)

        parent_item.appendRow(items)

        self.update_max_columns(len(items))

        index = self.index(parent_item.rowCount() - 1, 0, parent_item.index())
        element = self.element_from_index(index)
        self.element_added.emit(element)

    def update_max_columns(self, max_columns: int) -> None:
        # adds enough columns to match max_columns
        # this is necessary to set default items with flags
        # otherwise by default new columns are editable
        if max_columns > self.columnCount():
            missing_columns = max_columns - self.columnCount()
            for i in range(missing_columns):
                col = self.columnCount()
                items = []
                for row in range(self.rowCount()):
                    item = QtGui.QStandardItem()
                    item.setEditable(False)
                    items.append(item)
                self.insertColumn(col, items)

    def items_from_element(self, element: Element) -> list[QtGui.QStandardItem]:
        items = []
        fields = element.fields
        if len(element.fields) < self.columnCount():
            missing_columns = self.columnCount() - len(element.fields)
            fields.extend((Field() for _ in range(missing_columns)))
        for field in element.fields:
            item = QtGui.QStandardItem(field.name)
            if not element.movable:
                item.setDragEnabled(False)
            if element.no_children:
                item.setDropEnabled(False)
                item.setFlags(item.flags() | QtCore.Qt.ItemNeverHasChildren)
            if field.icon:
                item.setIcon(field.icon)
            if not field.editable:
                item.setEditable(False)

            items.append(item)
        return items

    def index_from_path(self, path: str) -> QtCore.QModelIndex:
        paths = path.split(os.sep)
        parent_index = QtCore.QModelIndex()
        for path in paths:
            for row in range(self.rowCount(parent_index)):
                index = self.index(row, 0, parent_index)
                item = self.itemFromIndex(index)
                if item and item.text() == path:
                    if path == paths[-1]:
                        return index
                    else:
                        parent_index = index
                        break
        return QtCore.QModelIndex()

    def unique_name(self, name: str, parent: QtCore.QModelIndex | None = None) -> str:
        parent = parent or QtCore.QModelIndex()

        children = []
        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if index.isValid():
                children.append(index.data())

        return unique_name(name, children)

    def setData(
        self,
        index,
        value: typing.Any,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.EditRole,
    ) -> typing.Any:
        previous = self.element_from_index(index)
        result = super().setData(index, value, role)
        if result:
            current = self.element_from_index(index)
            self.element_changed.emit(current, previous)
        return result

    def path_from_index(self, index: QtCore.QModelIndex) -> str:
        index = index.siblingAtColumn(0)
        if not index.isValid() or not index.data():
            return ''

        paths = [index.data()]
        while index.parent().isValid():
            index = index.parent()
            paths.insert(0, index.data())
        path = os.path.join(*paths)
        return path

    def element_from_index(self, index: QtCore.QModelIndex) -> Element | None:
        if not index.isValid():
            return

        fields = []
        element = Element(fields)
        for col in range(self.columnCount(index.parent())):
            item = self.itemFromIndex(index.siblingAtColumn(col))
            if item:
                icon = item.icon() or None
                editable = item.isEditable()
                fields.append(Field(item.text(), icon=icon, editable=editable))
                if col == 0:
                    element.movable = item.isDragEnabled()
                    element.no_children = bool(
                        item.flags() & QtCore.Qt.ItemNeverHasChildren
                    )
                    element.path = self.path_from_index(index)
        if fields:
            element.fields = fields
            return element

    def removeRow(
        self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        index = self.index(row, 0, parent)
        element = self.element_from_index(index)
        self.element_removed.emit(element)
        return super().removeRow(row, parent)


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
        is_left_dir = bool(source_left.flags() & QtCore.Qt.ItemNeverHasChildren)
        is_right_dir = bool(source_right.flags() & QtCore.Qt.ItemNeverHasChildren)
        result = super().lessThan(source_left, source_right)

        if is_left_dir and not is_right_dir:
            return False
        elif is_right_dir and not is_left_dir:
            return False
        else:
            return result


class ElementTree(QtWidgets.QTreeView):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setAlternatingRowColors(True)

        palette = self.palette()
        palette.setColor(
            QtGui.QPalette.AlternateBase, palette.color(QtGui.QPalette.Window)
        )
        self.setPalette(palette)

        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setSortingEnabled(True)
        self.setAutoExpandDelay(500)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if self.dragDropMode() == QtWidgets.QAbstractItemView.InternalMove:
            if event.dropAction() == QtCore.Qt.MoveAction:
                self.update_current_elements()
        super().dropEvent(event)

    def update_current_elements(self) -> None:
        # used for tracking elements about to be moved
        model = self.model().sourceModel()
        model.current_elements = self.selected_elements()

    def current_index(self) -> None:
        indices = self.selectionModel().selectedRows()
        index = (
            self.model().mapToSource(indices[0]) if indices else QtCore.QModelIndex()
        )
        return index

    def selected_elements(self) -> list[Element]:
        indices = self.selectionModel().selectedRows()
        proxy = self.model()
        model = proxy.sourceModel()
        elements = []
        for index in indices:
            index = proxy.mapToSource(index)
            if index.isValid():
                elements.append(model.element_from_index(index))
        return elements


class ElementBrowser(QtWidgets.QWidget):
    unique_names = True
    edit_requested = QtCore.Signal(Element)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.model = None
        self.proxy = None
        self.tree = None
        self.toolbar = None

        self._init_model()
        self._init_ui()

    def _init_model(self):
        self.model = ElementModel(parent=self)
        self.model.setHorizontalHeaderLabels(['Name'])
        self.proxy = ElementProxyModel(parent=self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setRecursiveFilteringEnabled(True)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setAutoAcceptChildRows(True)
        self.proxy.setDynamicSortFilter(False)

    def _init_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())

        self.toolbar = QtWidgets.QToolBar()
        self.layout().addWidget(self.toolbar)

        icon = MaterialIcon('add')
        action = QtWidgets.QAction(icon, 'Add Element', self)
        action.triggered.connect(lambda: self.add_element())
        self.toolbar.addAction(action)

        icon = MaterialIcon('remove')
        action = QtWidgets.QAction(icon, 'Remove Element', self)
        action.triggered.connect(self.remove_selected_elements)
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
        self.layout().addWidget(self.tree)

    def filter(self, text: str) -> None:
        self.tree.collapseAll()
        self.proxy.setFilterWildcard(text)
        if text:
            self.tree.expandAll()

    def add_element(self, name: str = 'New Element') -> Element:
        parent = self.tree.current_index()

        # if parent doesn't allow children, append as sibling
        parent_item = self.model.itemFromIndex(parent)
        if parent_item and parent_item.flags() & QtCore.Qt.ItemNeverHasChildren:
            parent = parent.parent()

        if self.unique_names:
            name = self.model.unique_name(name, parent)

        fields = [Field(name, editable=True)]
        element = Element(fields, no_children=True)

        self.model.append_element(element, parent)
        return element

    def add_group(self, name: str = 'New Group') -> Element:
        parent = self.tree.current_index()

        # if parent doesn't allow children, append as sibling
        parent_item = self.model.itemFromIndex(parent)
        if parent_item and parent_item.flags() & QtCore.Qt.ItemNeverHasChildren:
            parent = parent.parent()

        if self.unique_names:
            name = self.model.unique_name(name, parent)

        icon = MaterialIcon('folder')
        fields = [
            Field(name, icon=icon, editable=True),
        ]
        element = Element(fields)

        self.model.append_element(element, parent)
        return element

    def remove_selected_elements(self) -> None:
        indices = self.tree.selectionModel().selectedRows()

        if not indices:
            return

        text = 'Are you sure you want to permanently remove {} and all {} contents?'
        if len(indices) == 1:
            index = self.proxy.mapToSource(indices[0])
            item = self.model.itemFromIndex(index)
            text = text.format(item.text(), 'its')
        else:
            text = text.format('the selected elements', 'their')
        result = QtWidgets.QMessageBox.question(self, 'Delete', text)
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return

        indices = [
            QtCore.QPersistentModelIndex(self.proxy.mapToSource(index))
            for index in indices
        ]
        for index in indices:
            if index.isValid():
                self.model.removeRow(index.row(), index.parent())

    def action(self, name: str) -> QtWidgets.QAction:
        for action in self.toolbar.actions():
            if name == action.text():
                return action
