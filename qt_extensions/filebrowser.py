import dataclasses
import logging
import sys
import os
import shutil
from typing import Any

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.icons import MaterialIcon
from qt_extensions.elementbrowser import (
    ElementBrowser,
    Field,
    ElementDelegate,
    check_flag,
)


@dataclasses.dataclass
class FileElement:
    name: str
    path: str


class FileNameDelegate(ElementDelegate):
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
    def __init__(
        self,
        path: str,
        fields: list[Field] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(fields, parent)

        self.path = path
        self.file_filter = ''
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
            parent = self.model.find_index(root, Field('path'))

            for name in dirs:
                path = os.path.join(root, name)
                self._append_dir(path, parent)
            for name in files:
                path = os.path.join(root, name)
                self._append_file(path, parent)

        self.proxy.sort(0)
        self.tree.resize_columns()

    def add_element(self):
        parent = self._selected_index()

        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        path = os.path.join(parent_path, 'New File')
        self._append_file(path, parent)

    def add_group(self):
        parent = self._selected_index()

        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        path = os.path.join(parent_path, 'New Folder')
        self._append_dir(path, parent)

    def refresh(self) -> None:
        self.model.clear()
        self.sync_files = False
        self.init_elements()
        self.sync_files = True

    def file_add_element(self, element: FileElement) -> None:
        if not self.sync_files:
            return

        # what might be better is to check where the element was creaeted, then create the file based on that, then update the element

        index = self.model.find_index(element)
        if not index.isValid():
            return
        try:
            if check_flag(index, QtCore.Qt.ItemNeverHasChildren):
                # element is a file
                if not os.path.isdir(os.path.dirname(element.path)):
                    os.makedirs(element.path)
                f = open(element.path, 'x')
                f.close()
            else:
                # element is a dir
                os.makedirs(element.path)

        except (FileExistsError, PermissionError, FileNotFoundError) as e:
            logging.debug(e)
            self.refresh()

    def file_remove_element(self, element: FileElement) -> None:
        if os.path.isdir(element.path):
            shutil.rmtree(element.path)
        elif os.path.isfile(element.path):
            os.remove(element.path)
        # self.refresh()

    def file_move_element(
        self, element: FileElement, parent: QtCore.QModelIndex
    ) -> None:
        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        destination_path = os.path.join(parent_path, os.path.basename(element.path))
        source_path = element.path
        if destination_path == source_path:
            return

        try:
            if os.path.exists(destination_path):
                raise FileExistsError(f'File Exists: {destination_path}')
            shutil.move(source_path, destination_path)
            element.path = destination_path
            logging.debug(element.path)
        except (FileExistsError, PermissionError, FileNotFoundError) as e:
            logging.debug(e)
            self.refresh()

        # text = 'Are you sure you want to permanently remove {} and all {} contents?'
        # if len(indices) == 1:
        #     index = self.proxy.mapToSource(indices[0])
        #     item = self.model.itemFromIndex(index)
        #     text = text.format(item.text(), 'its')
        # else:
        #     text = text.format('the selected elements', 'their')
        # result = QtWidgets.QMessageBox.question(self, 'Delete', text)
        # if result == QtWidgets.QMessageBox.StandardButton.No:
        #     return

    def _append_dir(self, path: str, parent: QtCore.QModelIndex):
        name = os.path.basename(path)
        element = FileElement(name=name, path=path)
        icon = MaterialIcon('folder')
        self.model.append_element(element, icon=icon, parent=parent)

    def _append_file(self, path: str, parent: QtCore.QModelIndex):
        if not path.endswith(self.file_filter):
            return
        name = os.path.basename(path)
        element = FileElement(name=name, path=path)
        self.model.append_element(element, no_children=True, parent=parent)


def main():
    from qt_extensions import theme

    app = QtWidgets.QApplication(sys.argv)
    logging.getLogger().setLevel(logging.DEBUG)

    theme.apply_theme(theme.monokai)

    dialog = FileBrowser(
        r'D:\files\dev\027_flare\qt-extensions\qt_extensions',
        [Field('name'), Field('path')],
    )
    dialog.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
