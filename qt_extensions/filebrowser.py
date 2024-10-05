from __future__ import annotations

import dataclasses
import logging
import os
import shutil
from typing import Sequence

from PySide2 import QtWidgets, QtCore, QtGui
from qt_material_icons import MaterialIcon

from qt_extensions.elementbrowser import ElementBrowser, Field, ElementDelegate
from qt_extensions.helper import unique_path

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FileElement:
    name: str
    path: str


class FileNameDelegate(ElementDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        file_regex = QtCore.QRegularExpression(r'[\w\d\.-]+')
        self.validator = QtGui.QRegularExpressionValidator(file_regex, self)

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
        def set_selection() -> None:
            editor.selectionChanged.disconnect(set_selection)
            text = editor.text()
            root, ext = os.path.splitext(text)
            editor.setSelection(0, len(root))

        editor.selectionChanged.connect(set_selection)


class FileBrowser(ElementBrowser):
    dir_name = 'Unnamed'
    file_name = 'Unnamed'
    file_filter = ''
    sync_files = True

    def __init__(
        self,
        path: str,
        fields: Sequence[Field] = (),
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(fields, parent)

        self.path = os.path.normpath(path)

        self._init_elements()

        self.model.element_moved.connect(self._move_element)
        self.model.element_changed.connect(self._change_element)

    def _init_ui(self) -> None:
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
            if os.path.normpath(root) == self.path:
                parent = QtCore.QModelIndex()
            elif indexes:
                parent = indexes[0]
            else:
                break

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

    def add_element(self) -> QtCore.QModelIndex:
        parent = self._current_parent()

        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        path = os.path.join(parent_path, self.file_name)
        path = unique_path(path)

        try:
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(path)
            f = open(path, 'x')
            f.close()
        except OSError as e:
            logger.exception(e)
            return QtCore.QModelIndex()
        index = self._append_file(path, parent)
        return index

    def add_group(self) -> QtCore.QModelIndex:
        parent = self._current_parent()

        parent_element = self.model.element(parent)
        if isinstance(parent_element, FileElement):
            parent_path = parent_element.path
        else:
            parent_path = self.path

        path = os.path.join(parent_path, self.dir_name)
        path = unique_path(path)

        try:
            os.makedirs(path)
        except OSError as e:
            logger.exception(e)
            return QtCore.QModelIndex()
        index = self._append_dir(path, parent)
        return index

    def duplicate_selected(self) -> tuple[QtCore.QModelIndex, ...]:
        indexes = []
        for index in self.tree.selected_indexes:
            element = self.model.element(index)
            path = unique_path(element.path)
            try:
                shutil.copy(element.path, path)
            except OSError as e:
                logger.exception(e)
                continue
            copied_index = self.model.duplicate_index(index)
            copied_element = self.model.element(copied_index)
            copied_element.path = path
            self.model.refresh_index(copied_index)
            indexes.append(copied_index)
        return tuple(indexes)

    def refresh(self) -> None:
        self.blockSignals(True)
        elements = self.selected_elements()

        self.model.clear()

        self.sync_files = False
        self._init_elements()
        self.sync_files = True

        self.select_elements(elements)
        self.blockSignals(False)

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
            logger.exception(e)
            return
        super().remove_selected()

    def _append_dir(self, path: str, parent: QtCore.QModelIndex) -> QtCore.QModelIndex:
        name = os.path.basename(path)
        element = FileElement(name=name, path=path)
        icon = MaterialIcon('folder')
        index = self.model.append_element(element, icon=icon, parent=parent)
        return index

    def _append_file(self, path: str, parent: QtCore.QModelIndex) -> QtCore.QModelIndex:
        name = os.path.basename(path)
        element = FileElement(name=name, path=path)
        index = self.model.append_element(element, no_children=True, parent=parent)
        return index

    def _change_element(self, element: FileElement, previous: FileElement) -> None:
        if element.name == previous.name:
            return
        source_path = previous.path
        parent_path = os.path.dirname(previous.path)
        destination_path = unique_path(os.path.join(parent_path, element.name))
        try:
            shutil.move(source_path, destination_path)
        except OSError as e:
            logger.exception(e)
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
            logger.exception(e)
        self.refresh()
