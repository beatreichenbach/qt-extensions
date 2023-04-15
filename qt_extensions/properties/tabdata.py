import logging
import numbers
import typing

from PySide2 import QtWidgets, QtGui, QtCore

from qt_extensions.properties import PropertyWidget, IntProperty, FloatProperty
from qt_extensions import helper
from qt_extensions.icons import MaterialIcon
from qt_extensions.resizegrip import ResizeGrip


class StyledItemDelegate(QtWidgets.QStyledItemDelegate):
    def set_edit_data(
        self,
        value: typing.Any,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex,
    ) -> None:
        indexes = self.selected_indexes(index)
        model.blockSignals(True)
        for index in indexes:
            if index == indexes[-1]:
                model.blockSignals(False)
            model.setData(index, value, QtCore.Qt.EditRole)

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex,
    ) -> None:
        indexes = self.selected_indexes(index)
        model.blockSignals(True)
        for index in indexes:
            if index == indexes[-1]:
                model.blockSignals(False)
            super().setModelData(editor, model, index)

    def selected_indexes(self, current_index: QtCore.QModelIndex | None):
        indexes = []
        if self.parent():
            indexes = self.parent().selectedIndexes()
        if current_index is not None and current_index not in indexes:
            indexes.append(current_index)
        return indexes


class IntegerDelegate(StyledItemDelegate):
    def displayText(self, value: typing.Any, locale: QtCore.QLocale) -> str:
        return str(value)

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> QtWidgets.QWidget:

        editor = IntProperty(parent=parent)
        editor.slider_visible = False
        editor.line.setFrame(False)
        editor.commit_on_edit = True
        return editor

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex
    ) -> None:
        value = index.model().data(index, QtCore.Qt.EditRole)
        if value:
            editor.value = value

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex,
    ) -> None:
        value = editor.value
        self.set_edit_data(value, model, index)

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)


class FloatDelegate(StyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.decimals = None

    def displayText(self, value: typing.Any, locale: QtCore.QLocale) -> str:
        if self.decimals is not None:
            return f'{value:.{self.decimals}f}'.rstrip('0').rstrip('.')
        else:
            return f'{value}'.rstrip('0').rstrip('.')

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> QtWidgets.QWidget:
        editor = FloatProperty(parent=parent)
        editor.slider_visible = False
        editor.decimals = 6
        editor.line.setFrame(False)
        editor.commit_on_edit = True
        return editor

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex
    ) -> None:
        value = index.model().data(index, QtCore.Qt.EditRole)
        if value:
            editor.value = value

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex,
    ) -> None:
        value = editor.value
        self.set_edit_data(value, model, index)

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)


class DataTableModel(QtGui.QStandardItemModel):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.types = []

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: typing.Any,
        role: int = QtCore.Qt.EditRole,
    ) -> bool:
        if role == QtCore.Qt.EditRole:
            column = index.column()
            typ = self.types[column] if column < len(self.types) else None
            if typ is not None:
                try:
                    value = typ(value)
                except (ValueError, TypeError):
                    value = None
        return super().setData(index, value, role)


class DataTableView(QtWidgets.QTableView):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)

        self.horizontalHeader().setSortIndicatorShown(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setStretchLastSection(True)

        # header.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )

        # context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.context_menu = QtWidgets.QMenu(self)

        action = QtWidgets.QAction("Edit", self)
        action.triggered.connect(self.edit_selected)
        self.addAction(action)
        self.context_menu.addAction(action)

        action = QtWidgets.QAction("Copy", self)
        action.setShortcut(QtGui.QKeySequence.Copy)
        action.triggered.connect(self.copy_selected)
        self.addAction(action)
        self.context_menu.addAction(action)

        action = QtWidgets.QAction("Paste", self)
        action.setShortcut(QtGui.QKeySequence.Paste)
        action.triggered.connect(self.paste_selected)
        self.addAction(action)
        self.context_menu.addAction(action)

    def copy_selected(self) -> None:
        selected_indexes = self.selectedIndexes()
        if not self.model():
            return

        # create nested list from data
        data = []
        row_data = []
        row = 0
        for index in selected_indexes:
            if row != index.row() and row_data:
                data.append(row_data)
                row_data = []
            row = index.row()
            row_data.append(self.model().data(index))
        if row_data:
            data.append(row_data)

        # copy to clipboard
        text = '\n'.join('\t'.join(str(d) for d in row_data) for row_data in data)
        clipboard = QtGui.QClipboard()
        clipboard.setText(text)

    def edit_selected(self) -> None:
        index = self.currentIndex()
        if index.isValid():
            self.edit(index)

    def paste_selected(self) -> None:
        selected_indexes = self.selectedIndexes()
        current_index = self.currentIndex()
        if not current_index and not selected_indexes or not self.model():
            return

        # get top left index
        for index in selected_indexes:
            if (
                index.row() <= current_index.row()
                and index.column() <= current_index.column()
            ):
                current_index = index

        # get data
        text = QtGui.QClipboard().text()
        data = (row_text.split('\t') for row_text in text.split('\n'))

        # set data
        for row, row_data in enumerate(data):
            row_index = current_index.siblingAtRow(current_index.row() + row)
            if not row_index.isValid():
                continue
            for column, d in enumerate(row_data):
                index = row_index.siblingAtColumn(current_index.column() + column)
                if not index.isValid():
                    continue
                self.model().setData(index, d)

    def show_menu(self, position: QtCore.QPoint) -> None:
        self.context_menu.exec_(self.viewport().mapToGlobal(position))


class TabDataProperty(PropertyWidget):
    # https://pypi.org/project/tabulate/
    # property to display tabular data in a QTreeWidget
    # TODO: add support for numpy lists

    value_changed: QtCore.Signal = QtCore.Signal(list)

    value: list | None = None
    default: list | None = None
    headers: list | None = None
    types: list | None = None
    start_index: int = 0
    decimals: int = 3

    def __init__(
        self, name: str | None = None, parent: QtWidgets.QWidget | None = None
    ) -> None:
        self._delegates = []
        super().__init__(name, parent)

    def _init_ui(self) -> None:
        QtWidgets.QWidget().setLayout(self.layout())
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # table view
        self.model = DataTableModel(parent=self)
        self.model.itemChanged.connect(self._item_change)
        # self.model.dataChanged.connect(self.)
        self.view = DataTableView(parent=self)
        self.view.setModel(self.model)
        self.view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.layout().addWidget(self.view)

        # toolbar
        self.toolbar = QtWidgets.QToolBar()
        size = self.toolbar.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self.toolbar.setIconSize(QtCore.QSize(size, size))
        self.layout().addWidget(self.toolbar)

        icon = MaterialIcon('add')
        action = QtWidgets.QAction(icon, 'Add Row', self)
        action.triggered.connect(self.add_row)
        self.toolbar.addAction(action)

        icon = MaterialIcon('remove')
        action = QtWidgets.QAction(icon, 'Remove Row', self)
        action.triggered.connect(self.remove_row)
        self.toolbar.addAction(action)

        icon = MaterialIcon('clear_all')
        action = QtWidgets.QAction(icon, 'Clear', self)
        action.triggered.connect(self.clear)
        self.toolbar.addAction(action)

        self.resize_grip = ResizeGrip(self.view)
        self.resize_grip.can_resize_horizontal = True

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('headers', lambda _: self.update_horizontal_headers())
        self.setter_signal('start_index', lambda _: self.update_vertical_headers())
        self.setter_signal('decimals', self.set_decimals)
        self.setter_signal('types', self.set_types)

    def _item_change(self) -> None:
        self._value = self._tab_data_value()

    def _tab_data_value(self):
        value = []
        for row in range(self.model.rowCount()):
            row_values = []
            for column in range(self.model.columnCount()):
                index = self.model.index(row, column)
                column_value = self.model.data(index, QtCore.Qt.EditRole)
                row_values.append(column_value)
            value.append(row_values)
        return value

    def clear(self):
        self.model.clear()
        super().set_value([])
        self.update_horizontal_headers()

    def update_horizontal_headers(self) -> None:
        if self.headers:
            labels = list(map(helper.title, self.headers))
        else:
            labels = list(map(str, range(self.model.columnCount())))

        # for i, label in enumerate(labels):
        #     item = QtGui.QStandardItem()
        #     item.setText(label)
        #     self.model.setHorizontalHeaderItem(i, item)

        self.model.setHorizontalHeaderLabels(labels)
        self.resize_headers()

    def update_vertical_headers(self) -> None:
        rows = range(self.start_index, self.model.rowCount() + self.start_index)
        labels = list(map(str, rows))
        self.model.setVerticalHeaderLabels(labels)

    def set_types(self, types: list | tuple | None) -> None:
        self._delegates = []
        # fill up to column count
        if types is None:
            types = []
        types += [None] * (self.model.columnCount() - len(types))
        self.model.types = types

        for i, type_ in enumerate(types):
            if issubclass(type_, float):
                delegate = FloatDelegate(self.view)
            elif issubclass(type_, int):
                delegate = IntegerDelegate(self.view)
            else:
                delegate = StyledItemDelegate(self.view)
            self.view.setItemDelegateForColumn(i, delegate)
            self._delegates.append(delegate)

    def set_decimals(self, decimals: int) -> None:
        for delegate in self._delegates:
            if isinstance(delegate, FloatDelegate):
                delegate.decimals = decimals

    def set_value(self, value: list | None) -> None:
        self.model.clear()
        if value is None:
            return

        for row, row_data in enumerate(value):
            items = []
            if isinstance(row_data, dict):
                row_data = row_data.values()
            for column, cell_data in enumerate(row_data):
                item = QtGui.QStandardItem()
                if isinstance(cell_data, float):
                    cell_data = round(cell_data, self.decimals)
                item.setData(cell_data, QtCore.Qt.EditRole)
                items.append(item)
            if items:
                self.model.appendRow(items)

        super().set_value(self._tab_data_value())
        self.update_horizontal_headers()
        self.update_vertical_headers()

    def add_row(self) -> None:
        items = []
        for i in range(self.model.columnCount()):
            item = QtGui.QStandardItem()
            if i < len(self.types):
                type_ = self.types[i]
                if issubclass(type_, numbers.Number):
                    item.setData(0, QtCore.Qt.EditRole)
                elif issubclass(type_, str):
                    item.setData('', QtCore.Qt.EditRole)
            items.append(item)
        self.model.insertRow(self.model.rowCount(), items)
        self._item_change()
        self.update_vertical_headers()

    def remove_row(self) -> None:
        self.model.takeRow(self.model.rowCount() - 1)
        self._item_change()

    def resize_headers(self) -> None:
        header = self.view.horizontalHeader()
        for i in range(header.count()):
            size = max(self.view.sizeHintForColumn(i), header.sectionSizeHint(i))
            self.view.setColumnWidth(i, size)


__all__ = ['TabDataProperty']
