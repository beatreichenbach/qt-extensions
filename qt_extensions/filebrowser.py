import logging
import sys
import os
import shutil

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.icons import MaterialIcon
from qt_extensions.elementbrowser import ElementBrowser, Element, Field


class FileNameDelegate(QtWidgets.QStyledItemDelegate):
    item_changed = QtCore.Signal(str, QtCore.QAbstractItemModel, QtCore.QModelIndex)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        regex = QtCore.QRegularExpression(r'[\w\d\.-]+')
        self.validator = QtGui.QRegularExpressionValidator(regex, self)

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> QtWidgets.QWidget:
        editor = super().createEditor(parent, option, index)
        if self.validator:
            editor.setValidator(self.validator)
        return editor

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex
    ) -> None:
        super().setEditorData(editor, index)

        # selectAll gets called after opening the editor
        def set_selection():
            editor.selectionChanged.disconnect(set_selection)
            text = editor.text()
            root, ext = os.path.splitext(text)
            editor.setSelection(0, len(root))

        editor.selectionChanged.connect(set_selection)


class FileBrowser(ElementBrowser):
    # ignore_patterns = None

    def __init__(self, path: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.path = path
        self.sync_files = True

        self.init_elements()

        self.model.element_added.connect(self.file_add_element)
        self.model.element_removed.connect(self.file_remove_element)
        self.model.element_changed.connect(self.file_move_element)
        self.model.element_moved.connect(self.file_move_element)

    def _init_ui(self):
        super()._init_ui()

        delegate = FileNameDelegate(parent=self)
        self.tree.setItemDelegateForColumn(0, delegate)

        icon = MaterialIcon('refresh')
        action = QtWidgets.QAction(icon, 'Refresh', self)
        action.triggered.connect(self.refresh)
        self.toolbar.addAction(action)

    def init_elements(self) -> None:
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

    def refresh(self) -> None:
        self.model.clear()
        self.sync_files = False
        self.init_elements()
        self.sync_files = True

    def element_from_path(self, path: str) -> Element:
        name = os.path.basename(path)
        if os.path.isdir(path):
            icon = MaterialIcon('folder')
            fields = [Field(name, editable=True, icon=icon)]
            element = Element(fields)
        else:
            fields = [Field(name, editable=True)]
            element = Element(fields, no_children=True)
        return element

    def file_add_element(self, element: Element) -> None:
        if not self.sync_files:
            return

        path = os.path.join(self.path, element.path)

        try:
            if element.no_children:
                # element is a file
                if not os.path.isdir(os.path.dirname(path)):
                    os.makedirs(path)
                f = open(path, 'x')
                f.close()
            else:
                # element is a dir
                os.makedirs(path)

        except (FileExistsError, PermissionError, FileNotFoundError) as e:
            logging.debug(e)
            self.refresh()

    def file_remove_element(self, element: Element) -> None:
        path = os.path.join(self.path, element.path)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
        # self.refresh()

    def file_move_element(self, current: Element, previous: Element) -> None:
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
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    path = r'/flare/presets/lens'
    widget = FileBrowser(path)
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
