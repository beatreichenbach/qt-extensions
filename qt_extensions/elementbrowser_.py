import copy
import logging
import os
import dataclasses
import sys
from typing import Any, Optional

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.icons import MaterialIcon
from qt_extensions.helper import unique_name, title


@dataclasses.dataclass
class Field:
    name: str = ''
    label: str | None = None
    editable: bool = False

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = title(self.name)


class Element(QtCore.QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._index = None
        self.data = None
        self.icon = None
        self.deletable = True
        self.movable = True
        self.no_children = False
        self.required_parent = None

    # def __deepcopy__(self):
    #     element = Element()
    #     element.data = self.data  # data
    #     element.icon = self.icon  # icon
    #     element.deletable = self.deletable
    #     element.movable = self.movable  # draggable
    #     element.no_children = self.no_children  # never has children
    #     element.required_parent = self.required_parent
    #     return element

    def append_element(self, element: 'Element') -> None:
        self.model().append_element(element, self)

    def child(self, row: int) -> Optional['Element']:
        child_index = self.model().index(row, 0, self.index())
        element = self.model().element_from_index(child_index)
        return element

    def clone(self) -> 'Element':
        return copy.deepcopy(self)

    def index(self) -> QtCore.QModelIndex:
        # if self._index is None:
        #     self._index = QtCore.QModelIndex()
        return self._index

    def insert_element(self, row: int, element: 'Element') -> None:
        pass

    def model(self) -> 'ElementModel':
        return self.index().model()

    def parent(self) -> Optional['Element']:
        element = self.index().parent().data(QtCore.Qt.UserRole)
        return element

    def parents(self) -> list['Element']:
        parents = []
        try:
            index = self.index()
            while index.isValid():
                element = index.data(QtCore.Qt.UserRole)
                parents.insert(0, element)
                index = index.parent()
        except AttributeError:
            pass
        return parents

    def remove_row(self, row: int) -> None:
        if not self.index() or not self.index().isValid():
            return
        self.model().removeRow(row, self.index())

    def row(self) -> int:
        if not self.index() or not self.index().isValid():
            return 0
        row = self.index().row()
        return row

    def row_count(self) -> int:
        if not self.index() or not self.index().isValid():
            return 0
        row_count = self.model().rowCount(self.index().parent())
        return row_count

    def value(self, field: Field) -> Any:
        try:
            value = getattr(self.data, field.name)
            return value
        except AttributeError:
            return self.data


class ElementModel(QtGui.QStandardItemModel):
    element_added: QtCore.Signal = QtCore.Signal(Element)
    element_changed: QtCore.Signal = QtCore.Signal(Element, Element)
    element_moved: QtCore.Signal = QtCore.Signal(Element, Element)
    element_removed: QtCore.Signal = QtCore.Signal(Element)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        # this is used to track elements about to be moved
        self.current_elements = None

        self.bold_groups = True

        self._fields = []
        self._inherit_icons = False

        # self.columnsInserted.connect(self._columns_insert)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Any:
        # if self.bold_groups and role == QtCore.Qt.FontRole:
        #     element = self.element_from_index(index)
        #     if element and not element.no_children:
        #         font = QtGui.QFont()
        #         font.setBold(True)
        #         return font
        return super().data(index, role)

    def dropMimeData(
        self,
        data: QtCore.QMimeData,
        action: QtCore.Qt.DropAction,
        row: int,
        column: int,
        parent: QtCore.QModelIndex,
    ) -> bool:
        if action == QtCore.Qt.MoveAction:
            self._element_move(parent)
        return super().dropMimeData(data, action, row, 0, parent.siblingAtColumn(0))

    def removeRow(
        self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        index = self.index(row, 0, parent)
        element = self.element_from_index(index)
        if element:
            self.element_removed.emit(element)
        return super().removeRow(row, parent)

    def setData(
        self,
        index,
        value: Any,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.EditRole,
    ) -> Any:
        # previous = self.element_from_index(index).clone()
        result = super().setData(index, value, role)
        # if result and previous:
        #     current = self.element_from_index(index)
        #     self.element_changed.emit(current, previous)
        return result

    @property
    def fields(self) -> list[Field]:
        return self._fields

    @fields.setter
    def fields(self, value: list[Field]) -> None:
        self._fields = value
        # self.update_max_columns(len(self._fields))
        self.refresh_header_labels()

    @property
    def inherit_icons(self) -> bool:
        return self._inherit_icons

    @inherit_icons.setter
    def inherit_icons(self, value: bool) -> None:
        self._inherit_icons = value
        for row in range(self.rowCount()):
            element = self.element_from_index(self.index(row, 0))
            self._update_icon(element)

    def append_element(self, element: Element, parent: Element | None = None) -> None:
        if parent:
            parent_item = self.itemFromIndex(parent.index())
        else:
            parent_item = self.invisibleRootItem()

        items = self._create_items(element)
        if items:
            parent_item.appendRow(items)
            # element._index = items[0].index()
            self._update_icon(element)

            self.element_added.emit(element)

    # def index_from_path(self, path: str) -> QtCore.QModelIndex:
    #     paths = path.split(os.sep)
    #     parent_index = QtCore.QModelIndex()
    #     for name in paths:
    #         for row in range(self.rowCount(parent_index)):
    #             index = self.index(row, 0, parent_index)
    #             element = index.data(QtCore.Qt.UserRole)
    #             if element and element.name == name:
    #                 if name == paths[-1]:
    #                     return index
    #                 else:
    #                     parent_index = index
    #                     break
    #     return QtCore.QModelIndex()

    def refresh_header_labels(self) -> None:
        labels = [field.label for field in self.fields]
        super().setHorizontalHeaderLabels(labels)

    # def unique_name(self, name: str, parent: Element | None = None) -> str:
    #     # helper function to get unique name based on first field as name attribute
    #
    #     if parent:
    #         parent_item = self._item_from_element(parent)
    #     else:
    #         parent_item = self.invisibleRootItem()
    #
    #     if not self.fields:
    #         return name
    #     name_field = self.fields[0]
    #
    #     children = []
    #     for row in range(parent_item.rowCount()):
    #         child = parent_item.child(row, 0)
    #         if child:
    #             element = child.data(QtCore.Qt.UserRole)
    #             if isinstance(element, Element):
    #                 try:
    #                     value = getattr(element.data, name_field.name)
    #                     children.append(value)
    #                 except AttributeError:
    #                     pass
    #
    #     return unique_name(name, children)

    # def update_max_columns(self, max_columns: int) -> None:
    #     # adds enough columns to match max_columns
    #     # this is necessary to set default items with flags
    #     # otherwise by default new columns are editable
    #     if max_columns > self.columnCount():
    #         missing_columns = max_columns - self.columnCount()
    #         for i in range(missing_columns):
    #             col = self.columnCount()
    #             items = []
    #             for row in range(self.rowCount()):
    #                 item = QtGui.QStandardItem()
    #                 item.setEditable(False)
    #                 items.append(item)
    #             self.insertColumn(col, items)

    @staticmethod
    def index_from_element(element: Element) -> QtCore.QModelIndex:
        return element.index()

    @staticmethod
    def element_from_index(index: QtCore.QModelIndex) -> Element | None:
        element = index.siblingAtColumn(0).data(QtCore.Qt.UserRole)
        return element

    def _create_items(self, element: Element) -> list[QtGui.QStandardItem]:
        items = []

        for field in self.fields:
            value = element.value(field)
            # item = QtGui.QStandardItem(value)
            item = QtGui.QStandardItem(str(value))
            # item.setData(value, QtCore.Qt.EditRole)
            if not element.movable:
                item.setDragEnabled(False)
            if element.no_children:
                item.setDropEnabled(False)
                item.setFlags(item.flags() | QtCore.Qt.ItemNeverHasChildren)
            # if not field.editable:
            #     item.setEditable(False)
            items.append(item)

        if items:
            item = items[0]
            item.setData(element, QtCore.Qt.UserRole)

        return items

    def _element_move(self, parent: QtCore.QModelIndex) -> None:
        if not parent.flags() & QtCore.Qt.ItemIsDropEnabled:
            return

        if self.current_elements:
            parent_path = self.path_from_index(parent)
            for element in self.current_elements:
                self._update_icon(element)
                name = os.path.basename(element.path)
                path = os.path.join(parent_path, name)
                previous = dataclasses.replace(element)
                previous.path = path
                self.element_moved.emit(previous, element)
            self.current_elements = None

    # def _columns_insert(
    #     self, parent: QtCore.QModelIndex, first: int, last: int
    # ) -> None:
    #     super().setHorizontalHeaderLabels(self.header_labels)

    # def _item_from_element(self, element: Element) -> QtGui.QStandardItem:
    #     for row in range(self.rowCount()):
    #         index = self.index(row, 0)
    #         data = self.data(index, QtCore.Qt.UserRole)
    #         if element == data:
    #             item = self.itemFromIndex(index)
    #             if item is not None:
    #                 return item
    #     return self.invisibleRootItem()

    def _update_icon(self, element: Element) -> None:
        return
        item = self.itemFromIndex(element.index())
        if not item:
            return
        if element.icon:
            item.setIcon(element.icon)
            return
        if self.inherit_icons:
            for parent in element.parents():
                if parent.icon:
                    item.setIcon(parent.icon)
                    return


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
        is_left_group = bool(source_left.flags() & QtCore.Qt.ItemNeverHasChildren)
        is_right_group = bool(source_right.flags() & QtCore.Qt.ItemNeverHasChildren)

        if is_left_group != is_right_group:
            return False
        else:
            result = super().lessThan(source_left, source_right)
            return result


class ElementTree(QtWidgets.QTreeView):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setSortingEnabled(True)
        self.setAutoExpandDelay(500)

        # alternate row colors
        # self.setAlternatingRowColors(True)
        # palette = self.palette()
        # palette.setColor(
        #     QtGui.QPalette.AlternateBase, palette.color(QtGui.QPalette.Window)
        # )
        # self.setPalette(palette)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if self.dragDropMode() == QtWidgets.QAbstractItemView.InternalMove:
            if event.dropAction() == QtCore.Qt.MoveAction:
                self._update_current_elements()
        super().dropEvent(event)

    def current_element(self) -> Element | None:
        indices = self.selectionModel().selectedRows()
        index = (
            self.model().mapToSource(indices[0]) if indices else QtCore.QModelIndex()
        )
        proxy = self.model()
        model = proxy.sourceModel()
        element = model.element_from_index(index)
        return element

    def selected_elements(self) -> list[Element]:
        indices = self.selectionModel().selectedRows()
        proxy = self.model()
        model = proxy.sourceModel()
        elements = []
        for index in indices:
            index = proxy.mapToSource(index)
            element = model.element_from_index(index)
            if element:
                elements.append(element)
        return elements

    def _update_current_elements(self) -> None:
        # used for tracking elements about to be moved
        proxy = self.model()
        model = proxy.sourceModel()
        model.current_indexes = self.selected_elements()


class ElementBrowser(QtWidgets.QWidget):
    unique_names = True
    edit_requested = QtCore.Signal(Element)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

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
        self.layout().addWidget(self.tree)

    def filter(self, text: str) -> None:
        self.tree.collapseAll()
        self.proxy.setFilterWildcard(text)
        if text:
            self.tree.expandAll()

    def add_element(self, element: Element | None = None) -> None:
        if element is None:
            element = Element()
            element.data = 'New Element'
            element.no_children = True

        parent = self.tree.current_element()
        if parent and parent.no_children:
            parent = parent.parent()

        # if self.unique_names:
        #     element.name = self.model.unique_name(element.name, parent)

        self.model.append_element(element, parent)

    def duplicate_element(self, element: Element | None = None):
        if element is None:
            element = self.tree.current_element()

        if element:
            parent = element.parent()
            duplicate = element.clone()
            self.model.append_element(duplicate, parent)

    def add_group(self, name: str = 'New Group') -> None:
        element = Element()
        element.data = 'New Group'
        element.icon = MaterialIcon('folder')
        self.add_element(element)

    # def add_group(self, name: str = 'New Group') -> Element:
    #     parent = self.tree.current_index()
    #
    #     # if parent doesn't allow children, append as sibling
    #     parent_item = self.model.itemFromIndex(parent)
    #     if parent_item and parent_item.flags() & QtCore.Qt.ItemNeverHasChildren:
    #         parent = parent.parent()
    #
    #     if self.unique_names:
    #         name = self.model.unique_name(name, parent)
    #
    #     icon = MaterialIcon('folder')
    #     fields = [
    #         Field(name, icon=icon, editable=True),
    #     ]
    #     element = Element(fields)
    #
    #     self.model.append_element(element, parent)
    #     return element

    # def duplicate_elements(self) -> None:
    #     indices = self.tree.selectionModel().selectedRows()
    #
    #     indices = [
    #         QtCore.QPersistentModelIndex(self.proxy.mapToSource(index))
    #         for index in indices
    #     ]
    #     if not indices:
    #         return
    #
    #     last_index = indices.pop()
    #     element = self.model.element_from_index(last_index)
    #
    #     parent_item = self.model.itemFromIndex(parent)
    #
    #     if self.unique_names:
    #         name = element.fields[0]
    #         name = self.model.unique_name(element, last_index.parent())
    #     self.model.append_element(element, parent)
    #
    #     parent = self.tree.current_index()
    #
    def remove_selected_elements(self) -> None:
        indices = self.tree.selectionModel().selectedRows()

        # build list of persistent indices so that indices don't changed
        # as rows are removed
        persistent_indices = [
            QtCore.QPersistentModelIndex(self.proxy.mapToSource(index))
            for index in indices
        ]
        for index in persistent_indices:
            if index.isValid():
                self.model.removeRow(index.row(), index.parent())

    def action(self, name: str) -> QtWidgets.QAction:
        for action in self.toolbar.actions():
            if name == action.text():
                return action


class Foo:
    pass


def main():
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    widget = ElementBrowser()
    widget.model.fields = [Field(name='name')]
    element = Element(widget.model)

    data = Foo()
    data.name = 1230.34
    element.data = widget.model
    widget.add_element(element)
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
