import dataclasses
import logging
import sys
import os
import shutil
import re
from typing import Any

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.helper import unique_name, unique_path
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
    file_filter = ''
    sync_files = True

    def __init__(
        self,
        path: str,
        fields: list[Field] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(fields, parent)

        self.path = path

        self._init_elements()

        self.model.element_moved.connect(self._move_element)
        self.model.element_changed.connect(self._change_element)

    def _init_ui(self):
        super()._init_ui()

        delegate = FileNameDelegate(parent=self)
        self.tree.setItemDelegateForColumn(0, delegate)

        icon = MaterialIcon('refresh')
        action = QtWidgets.QAction(icon, 'Refresh', self)
        action.triggered.connect(self.refresh)
        self.toolbar.addAction(action)

    def _init_elements(self) -> None:
        for root, dirs, files in os.walk(self.path):
            indexes = self.model.find_indexes(root, Field('path'))
            parent = indexes[0] if indexes else QtCore.QModelIndex()

            for name in dirs:
                path = os.path.join(root, name)
                self._append_dir(path, parent)
            for name in files:
                if not name.endswith(self.file_filter):
                    continue
                path = os.path.join(root, name)
                self._append_file(path, parent)

        self.proxy.sort(0)
        self.tree.resize_columns()

    def add_element(self):
        parent = self._current_parent()

        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        path = os.path.join(parent_path, 'Unnamed')
        path = unique_path(path)

        try:
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(path)
            f = open(path, 'x')
            f.close()
        except OSError as e:
            logging.warning(e)
            return
        return self._append_file(path, parent)

    def add_group(self):
        parent = self._current_parent()

        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        path = os.path.join(parent_path, 'Unnamed')
        path = unique_path(path)

        try:
            os.makedirs(path)
        except OSError as e:
            logging.warning(e)
            return
        return self._append_dir(path, parent)

    def duplicate_selected(self) -> None:
        # elements = []
        try:
            for element in self.selected_elements():
                path = unique_path(element.path)
                shutil.copy(element.path, path)
            elements = super().duplicate_selected()
        except OSError as e:
            logging.warning(e)
        # for element in elements:
        #     self.model.refresh_element(element)
        # return elements

    def refresh(self) -> None:
        self.model.clear()
        self.sync_files = False
        self._init_elements()
        self.sync_files = True

    def remove_selected(self) -> None:

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

        try:
            for element in self.selected_elements():
                if os.path.isdir(element.path):
                    shutil.rmtree(element.path)
                elif os.path.isfile(element.path):
                    os.remove(element.path)
        except OSError as e:
            logging.warning(e)
            return
        super().remove_selected()

    def _append_dir(self, path: str, parent: QtCore.QModelIndex):
        name = os.path.basename(path)
        element = FileElement(name=name, path=path)
        icon = MaterialIcon('folder')
        self.model.append_element(element, icon=icon, parent=parent)
        return element

    def _append_file(self, path: str, parent: QtCore.QModelIndex):
        name = os.path.basename(path)
        element = FileElement(name=name, path=path)
        self.model.append_element(element, no_children=True, parent=parent)
        return element

    def _change_element(self, element: FileElement, previous: FileElement) -> None:
        if element.name == previous.name:
            return
        source_path = previous.path
        parent_path = os.path.dirname(previous.path)
        destination_path = unique_path(os.path.join(parent_path, element.name))
        try:
            shutil.move(source_path, destination_path)
        except OSError as e:
            logging.warning(e)
        self.refresh()

    def _move_element(self, element: FileElement, parent: QtCore.QModelIndex) -> None:
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
        except OSError as e:
            logging.warning(e)

        self.refresh()


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
