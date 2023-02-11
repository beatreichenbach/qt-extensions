import logging
import sys
import re
import os
import dataclasses
import shutil
from enum import auto, Enum

from PySide2 import QtWidgets, QtCore, QtGui

from qtmaterialicons.icons import MaterialIcon

from flare.qt.utils import unique_name


@dataclasses.dataclass
class Field:
    name: str = ''
    icon: MaterialIcon = None
    editable: bool = False


@dataclasses.dataclass
class Element:
    fields: list[Field]
    moveable: bool = True
    no_children: bool = False
    path: str = ''


class ElementModel(QtGui.QStandardItemModel):
    element_added = QtCore.Signal(Element)
    element_changed = QtCore.Signal(Element, Element)
    element_moved = QtCore.Signal(Element, Element)
    element_removed = QtCore.Signal(Element)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.header_labels = []

        # this is used to track elements about to be moved
        self.current_elements = None
        self.rowsInserted.connect(self.rows_insert)

        self.columnsInserted.connect(self.columns_insert)

    def rows_insert(self, parent, first, last):
        self.last_parent = parent

    def columns_insert(self, parent, first, last):
        super().setHorizontalHeaderLabels(self.header_labels)

    def setHorizontalHeaderLabels(self, labels):
        # remember header labels in case data gets reset
        self.header_labels = labels
        self.update_max_columns(len(labels))
        super().setHorizontalHeaderLabels(labels)

    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.MoveAction:
            self.element_move(parent)
        return super().dropMimeData(data, action, row, 0, parent.siblingAtColumn(0))

    def element_move(self, parent):
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

    def append_element(self, element, parent=None):
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

    def update_max_columns(self, max_columns):
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

                for row in range(self.rowCount()):
                    item = self.item(row, col)

    def items_from_element(self, element):
        items = []
        fields = element.fields
        if len(element.fields) < self.columnCount():
            missing_columns = self.columnCount() - len(element.fields)
            fields.extend((Field() for i in range(missing_columns)))
        for field in element.fields:
            item = QtGui.QStandardItem(field.name)
            if not element.moveable:
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

    def index_from_path(self, path):
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

    def unique_name(self, name, parent=None):
        parent = parent or QtCore.QModelIndex()

        children = []
        for row in range(self.rowCount(parent)):
            index = self.index(row, 0, parent)
            if index.isValid():
                children.append(index.data())

        return unique_name(name, children)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        previous = self.element_from_index(index)
        result = super().setData(index, value, role)
        if result:
            current = self.element_from_index(index)
            self.element_changed.emit(current, previous)
        return result

    def path_from_index(self, index):
        index = index.siblingAtColumn(0)
        if not index.isValid() or not index.data():
            return ''

        paths = [index.data()]
        while index.parent().isValid():
            index = index.parent()
            paths.insert(0, index.data())
        path = os.path.join(*paths)
        return path

    def element_from_index(self, index):
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
                    element.moveable = item.isDragEnabled()
                    element.no_children = bool(
                        item.flags() & QtCore.Qt.ItemNeverHasChildren
                    )
                    element.path = self.path_from_index(index)
        if fields:
            element.fields = fields
            return element

    def removeRow(self, row, parent):
        index = self.index(row, 0, parent)
        element = self.element_from_index(index)
        self.element_removed.emit(element)
        super().removeRow(row, parent)


class ElementProxyModel(QtCore.QSortFilterProxyModel):
    # autoAcceptChildRows is a Qt6 feature
    _autoAcceptChildRows = False

    def autoAcceptChildRows(self):
        return self._autoAcceptChildRows

    def setAutoAcceptChildRows(self, value):
        self._autoAcceptChildRows = value

    def filterAcceptsRow(self, source_row, source_parent):
        if super().filterAcceptsRow(source_row, source_parent):
            return True
        if self.autoAcceptChildRows() and source_parent.isValid():
            source_row = source_parent.row()
            source_parent = source_parent.parent()
            return self.filterAcceptsRow(source_row, source_parent)
        return False

    def lessThan(self, source_left, source_right):
        is_left_dir = bool(source_left.flags() & QtCore.Qt.ItemNeverHasChildren)
        is_right_dir = bool(source_right.flags() & QtCore.Qt.ItemNeverHasChildren)
        result = super().lessThan(source_left, source_right)

        if is_left_dir and not is_right_dir:
            return False
        elif is_right_dir and not is_left_dir:
            return False
        else:
            return result


class FileNameDelegate(QtWidgets.QStyledItemDelegate):
    item_changed = QtCore.Signal(str, QtCore.QAbstractItemModel, QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        regex = r'[\w\d\.-]+'
        self.validator = QtGui.QRegularExpressionValidator(regex, self)

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if self.validator:
            editor.setValidator(self.validator)
        return editor

    def setEditorData(self, editor, index):
        super().setEditorData(editor, index)

        # selectAll gets called after opening the editor
        def set_selection():
            editor.selectionChanged.disconnect(set_selection)
            text = editor.text()
            root, ext = os.path.splitext(text)
            editor.setSelection(0, len(root))

        editor.selectionChanged.connect(set_selection)


class ElementTree(QtWidgets.QTreeView):
    def __init__(self, parent=None):
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

    def dropEvent(self, event):
        if self.dragDropMode() == QtWidgets.QAbstractItemView.InternalMove:
            if event.dropAction() == QtCore.Qt.MoveAction:
                self.update_current_elements()
        super().dropEvent(event)

    def update_current_elements(self):
        # used for tracking elements about to be moved
        model = self.model().sourceModel()
        model.current_elements = self.selected_elements()

    def current_index(self):
        indices = self.selectionModel().selectedRows()
        index = (
            self.model().mapToSource(indices[0]) if indices else QtCore.QModelIndex()
        )
        return index

    def selected_elements(self):
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

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_model()
        self.init_ui()
        self.init_toolbar()

    def init_model(self):
        self.model = ElementModel(parent=self)
        self.model.setHorizontalHeaderLabels(['Name'])
        self.proxy = ElementProxyModel(parent=self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setRecursiveFilteringEnabled(True)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setAutoAcceptChildRows(True)
        self.proxy.setDynamicSortFilter(False)

    def init_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())

        self.tree = ElementTree()
        self.tree.setModel(self.proxy)
        self.layout().addWidget(self.tree)

    def init_toolbar(self):
        self.toolbar = QtWidgets.QToolBar()
        self.layout().insertWidget(0, self.toolbar)

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

    def filter(self, text):
        self.tree.collapseAll()
        self.proxy.setFilterWildcard(text)
        if text:
            self.tree.expandAll()

    def add_element(self, name='New Element'):
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

    def add_group(self, name='New Group'):
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

    def remove_selected_elements(self):
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

    def action(self, name):
        for action in self.toolbar.actions():
            if name == action.text():
                return action


class FileBrowser(ElementBrowser):
    # ignore_patterns = None

    def __init__(self, path, parent=None):
        super().__init__(parent)

        self.path = path

        delegate = FileNameDelegate(parent=self)
        self.tree.setItemDelegateForColumn(0, delegate)

        self.init_elements()

        self.sync_files = True

        self.model.element_added.connect(self.file_add_element)
        self.model.element_removed.connect(self.file_remove_element)
        self.model.element_changed.connect(self.file_move_element)
        self.model.element_moved.connect(self.file_move_element)

        # update actions
        # action = self.action('Add Element')
        # action.setText('Add File')
        # action.disconnect()
        # action.triggered.connect(lambda: self.add_element('New File'))
        # action = self.action('Add Group')
        # action.setText('Add Folder')
        # action.disconnect()
        # action.triggered.connect(lambda: self.add_group('New Folder'))

        icon = MaterialIcon('refresh')
        action = QtWidgets.QAction(icon, 'Refresh', self)
        action.triggered.connect(self.refresh)
        self.toolbar.addAction(action)

    def init_elements(self):
        for root, dirs, files in os.walk(self.path):
            relative_path = os.path.relpath(root, self.path)
            parent = self.model.index_from_path(relative_path)
            for name in dirs:
                element = self.element_from_path(os.path.join(root, name))
                self.model.append_element(element, parent)
            for name in files:
                element = self.element_from_path(os.path.join(root, name))
                self.model.append_element(element, parent)
        # sort
        self.proxy.sort(0)

        # adjust column width
        self.tree.expandAll()
        for col in range(self.model.columnCount()):
            self.tree.resizeColumnToContents(col)
        self.tree.collapseAll()

    def refresh(self):
        self.model.clear()
        self.sync_files = False
        self.init_elements()
        self.sync_files = True

    def element_from_path(self, path):
        name = os.path.basename(path)
        if os.path.isdir(path):
            icon = MaterialIcon('folder')
            fields = [Field(name, editable=True, icon=icon)]
            element = Element(fields)
        else:
            fields = [Field(name, editable=True)]
            element = Element(fields, no_children=True)
        return element

    def file_add_element(self, element):
        if not self.sync_files:
            return

        path = os.path.join(self.path, element.path)

        try:
            if element.no_children:
                # element is file
                if not os.path.isdir(os.path.dirname(path)):
                    os.makedirs(path)
                f = open(path, 'x')
                f.close()
            else:
                # element is dir
                os.makedirs(path)

        except (FileExistsError, PermissionError, FileNotFoundError) as e:
            logging.debug(e)
            self.refresh()

    def file_remove_element(self, element):
        path = os.path.join(self.path, element.path)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
        # self.refresh()

    def file_move_element(self, current, previous):
        destination_path = os.path.join(self.path, current.path)
        source_path = os.path.join(self.path, previous.path)
        if destination_path == source_path:
            return

        try:
            if os.path.exists(destination_path):
                raise FileExistsError(f'File Exists: {destination_path}')
            shutil.move(source_path, destination_path)
        except (FileExistsError, PermissionError, FileNotFoundError) as e:
            logging.debug(e)
            self.refresh()


def main():
    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    path = r'/flare/presets/lens'
    widget = FileBrowser(path)
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
