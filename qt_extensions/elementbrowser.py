import copy
import dataclasses
import logging
import sys

from typing import Any

from PySide2 import QtGui, QtCore, QtWidgets

from qt_extensions.helper import title
from qt_extensions.icons import MaterialIcon


@dataclasses.dataclass
class Field:
    name: str = ''
    label: str | None = None
    editable: bool = False

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = title(self.name)


ItemFlags = QtCore.Qt.ItemFlags
ItemFlags.Deletable = 1 << 9


class Element:
    data: Any = None
    # icon: QtGui.QIcon | None = None
    # movable: bool = True
    # deletable: bool = True
    # no_children: bool = False
    require_ancestor = None
    ancestors: list['Element'] = []

    def __repr__(self):
        return repr(self.data)


def set_flag(item, flag: int, value: bool) -> None:
    if value:
        item.setFlags(item.flags() | flag)
    else:
        item.setFlags(item.flags() & ~flag)


def no_children(item: QtGui.QStandardItem | QtCore.QModelIndex) -> bool:
    return bool(item.flags() & QtCore.Qt.ItemNeverHasChildren)


def set_no_children(item, value: bool) -> None:
    set_flag(item, QtCore.Qt.ItemNeverHasChildren, value)


def movable(item) -> bool:
    return item.isDragEnabled()


def set_movable(item, value: bool) -> None:
    item.setDragEnabled(value)


def deletable(item) -> bool:
    return bool(item.flags() & ItemFlags.Deletable)


def set_deletable(item, value: bool) -> None:
    set_flag(item, ItemFlags.Deletable, value)


class ElementModel(QtGui.QStandardItemModel):
    element_added: QtCore.Signal = QtCore.Signal(Element)
    element_changed: QtCore.Signal = QtCore.Signal(Element, Element)
    element_moved: QtCore.Signal = QtCore.Signal(Element, Element)
    element_removed: QtCore.Signal = QtCore.Signal(Element)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        # # this is used to track elements about to be moved
        self.current_indexes = []

        self._elements = []
        self._fields = []
        self._bold_groups = True
        self.class_groups = False

    @property
    def bold_groups(self) -> bool:
        return self._bold_groups

    @bold_groups.setter
    def bold_groups(self, value: bool) -> None:
        self._bold_groups = value

    @property
    def fields(self) -> list[Field]:
        return self._fields

    @fields.setter
    def fields(self, value: list[Field]) -> None:
        self._fields = value
        self.refresh_header_labels()

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Any:
        if self.bold_groups and role == QtCore.Qt.FontRole:
            item = self.itemFromIndex(index)
            if not (item.flags() & QtCore.Qt.ItemNeverHasChildren):
                font = QtGui.QFont()
                font.setBold(True)
                return font
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
            self._index_move(parent)
        return super().dropMimeData(data, action, row, 0, parent.siblingAtColumn(0))

    def removeRow(
        self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> bool:
        # index = self.index(row, 0, parent)
        # element = self.itemFromIndex(index)
        # if element:
        #     self.element_removed.emit(element)
        return super().removeRow(row, parent)

    def setData(
        self,
        index,
        value: Any,
        role: int = QtCore.Qt.EditRole,
    ) -> Any:
        previous = copy.deepcopy(self.element_from_index(index))
        result = super().setData(index, value, role)
        if result and previous:
            current = self.element_from_index(index)
            self.element_changed.emit(current, previous)
        return result

    def append_element(
        self, element: Element, parent: Element | QtCore.QModelIndex | None = None
    ) -> None:
        parent_item = None
        if isinstance(parent, Element):
            parent_item = self.item_from_element(parent)
            if parent_item and parent.no_children:
                parent_item = parent_item.parent()

        elif isinstance(parent, QtCore.QModelIndex):
            parent_item = self.itemFromIndex(parent)
            parent_element = self.element_from_index(parent)
            if parent_item and parent_element and parent_element.no_children:
                parent_item = parent_item.parent()

        if parent_item is None:
            parent_item = self.invisibleRootItem()

        items = self._create_items(element)
        if items:
            # key = max(self._elements.keys()) + 1
            # self._elements[key] = element
            self._elements.append(element)
            parent_item.appendRow(items)
            item = items[0]
            key = len(self._elements) - 1
            item.setData(key, QtCore.Qt.UserRole)
            element.ancestors = self.ancestors(element)
            if element.icon:
                item.setIcon(element.icon)

        self.element_added.emit(element)

    def element_from_index(self, index: QtCore.QModelIndex) -> Element | None:
        element = None
        index = index.siblingAtColumn(0)
        key = index.data(QtCore.Qt.UserRole)
        if key:
            try:
                element = self._elements[key]
            except KeyError:
                pass
        return element

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

    def refresh_header_labels(self) -> None:
        labels = [field.label for field in self.fields]
        super().setHorizontalHeaderLabels(labels)

    def _create_items(self, element: Element) -> list[QtGui.QStandardItem]:
        items = []

        for field in self.fields:
            value = self.data_value(element.data, field)
            text = '' if value is None else str(value)
            item = QtGui.QStandardItem(text)

            if field.editable:
                item.setData(value, QtCore.Qt.EditRole)
            else:
                item.setEditable(False)

            set_movable(item, element.movable)
            set_no_children(item, element.no_children)
            set_deletable(item, element.deletable)

            items.append(item)
        return items

    def _index_move(self, parent: QtCore.QModelIndex) -> None:
        if not parent.isValid():
            # is root
            pass
        elif not (parent.flags() & QtCore.Qt.ItemIsDropEnabled):
            return

        if self.current_indexes:
            parent_element = self.element_from_index(parent)
            if parent_element:
                ancestors = [*self.ancestors(parent_element), parent_element]
            else:
                ancestors = []
            for index in self.current_indexes:
                previous = self.element_from_index(index)
                if not previous:
                    continue
                current = copy.copy(previous)

                current.ancestors = ancestors
                self.element_moved.emit(previous, current)
            self.current_indexes = None

    def item_from_element(
        self, element: Element, parent: QtCore.QModelIndex | None = None
    ) -> QtGui.QStandardItem | None:
        if parent is None:
            parent = QtCore.QModelIndex()

        try:
            key = self._elements.index(element)
        except ValueError:
            return

        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if index and key == index.data(QtCore.Qt.UserRole):
                return self.itemFromIndex(index)
            else:
                item = self.item_from_element(element, index)
                if item is not None:
                    return item

    def ancestors(self, element: Element) -> list[Element]:
        ancestors = []
        item = self.item_from_element(element)
        while item and item.parent():
            item = item.parent()
            element = self.element_from_index(item.index())
            if not element:
                break
            ancestors.insert(0, element)
        ancestors.reverse()
        return ancestors


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

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if self.dragDropMode() == QtWidgets.QAbstractItemView.InternalMove:
            if event.dropAction() == QtCore.Qt.MoveAction:
                self._update_current_indexes()
        super().dropEvent(event)

    # def current_element(self) -> Element | None:
    #     current_index = self.model().mapToSource(self.currentIndex())
    #     model = self.model().sourceModel()
    #     element = model.element_from_index(current_index)
    #     return element

    # def selected_elements(self) -> list[Element]:
    #     indices = self.selectionModel().selectedRows()
    #     proxy = self.model()
    #     model = proxy.sourceModel()
    #     elements = []
    #     for index in indices:
    #         index = proxy.mapToSource(index)
    #         element = model.element_from_index(index)
    #         if element:
    #             elements.append(element)
    #     return elements

    def _update_current_indexes(self) -> None:
        # used for tracking elements about to be moved
        model = self.model()
        indexes = self.selectionModel().selectedRows()
        if model.sourceModel():
            indexes = [model.mapToSource(index) for index in indexes]
            model = model.sourceModel()
        model.current_indexes = indexes


class ElementBrowser(QtWidgets.QWidget):
    unique_names = True
    # edit_requested = QtCore.Signal(Element)

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
        # action.triggered.connect(self.remove_selected_elements)
        self.toolbar.addAction(action)

        icon = MaterialIcon('content_copy')
        action = QtWidgets.QAction(icon, 'Duplicate', self)
        # action.triggered.connect(lambda: self.duplicate_element())
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

    def add_element(self, element: Element | None = None) -> Element:
        if element is None:
            element = Element()
            element.data = 'New Element'
            element.no_children = True

        parent = self.selected_index()
        # if parent and parent.no_children:
        #     parent = parent.parent()

        # if self.unique_names:
        #     element.name = self.model.unique_name(element.name, parent)

        self.model.append_element(element, parent)

        return element

    def add_group(self, element: Element | None = None) -> Element:
        if element is None:
            element = Element()
            element.data = 'New Group'
            element.icon = MaterialIcon('folder')

        parent = self.selected_index()

        self.model.append_element(element, parent)

        return element

    def selected_index(self) -> QtCore.QModelIndex:
        selected_indices = self.tree.selectedIndexes()
        if selected_indices:
            index = self.proxy.mapToSource(selected_indices[0])
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
    widget.model.fields = [Field(name='name')]
    widget.model.element_added.connect(lambda current: logging.info(current.ancestors))
    widget.model.element_removed.connect(
        lambda current: logging.info(current.ancestors)
    )
    widget.model.element_changed.connect(
        lambda previous, current: logging.info([previous.ancestors, current.ancestors])
    )
    widget.model.element_moved.connect(
        lambda previous, current: logging.info([previous.ancestors, current.ancestors])
    )

    data = 'Bob'

    # data = Foo()
    # data.name = 'Bobby'

    element = Element()
    element.data = data

    widget.add_element(element)
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
