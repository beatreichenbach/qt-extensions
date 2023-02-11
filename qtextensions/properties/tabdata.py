import logging
import numbers
import typing

from PySide2 import QtWidgets, QtGui, QtCore

from qtextensions.properties.widgets import PropertyWidget, IntProperty, FloatProperty
from qtextensions import helper
from qtextensions.icons import MaterialIcon
from qtextensions.resizegrip import ResizeGrip


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
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)

        # table view
        self.model = QtGui.QStandardItemModel(parent=self)
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

        self.resize_grip = ResizeGrip(self.view)
        self.resize_grip.can_resize_horizontal = True

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('headers', lambda _: self.update_horizontal_headers())
        self.setter_signal('start_index', lambda _: self.update_vertical_headers())
        self.setter_signal('decimals', self.set_decimals)
        self.setter_signal('types', self.set_types)

    def _item_change(self) -> None:
        value = []
        for row in range(self.model.rowCount()):
            row_values = []
            for column in range(self.model.columnCount()):
                index = self.model.index(row, column)
                column_value = self.model.data(index, QtCore.Qt.EditRole)
                row_values.append(column_value)
            value.append(row_values)

        self._value = value

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

    def set_types(self, types: list[typing.Type] | None) -> None:
        if types is None:
            return
        for i, type_ in enumerate(types):
            if issubclass(type_, float):
                delegate = FloatDelegate(self)
            elif issubclass(type_, int):
                delegate = IntegerDelegate(self)
            else:
                continue
            self.view.setItemDelegateForColumn(i, delegate)
            self._delegates.append(delegate)

    def set_decimals(self, decimals: int) -> None:
        for delegate in self._delegates:
            if isinstance(delegate, FloatDelegate):
                delegate.decimals = decimals

    def set_value(self, value: list | None) -> None:
        if value is None:
            return
        for row, row_data in enumerate(value):
            items = []
            for column, cell_data in enumerate(row_data):
                item = QtGui.QStandardItem()
                item.setData(cell_data, QtCore.Qt.EditRole)
                items.append(item)
            if items:
                self.model.appendRow(items)
        self.update_horizontal_headers()

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


class DataTableView(QtWidgets.QTableView):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
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


class IntegerDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

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
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)


class FloatDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.decimals = None

    def displayText(self, value: typing.Any, locale: QtCore.QLocale) -> str:
        if self.decimals is not None:
            return f'{value:.{self.decimals}f}'.rstrip('0').rstrip('.')
        else:
            return str(value)

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
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)


def main():
    import sys
    from qtextensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        ['A really big Star', 406320, 339023452345.23450],
    ]
    prop = TabDataProperty()
    prop.default = data
    prop.headers = ['Name', 'Radius', 'Weight']
    prop.types = [str, int, float]
    prop.start_index = 4
    prop.show()
    sys.exit(app.exec_())


__all__ = ['TabDataProperty']


if __name__ == '__main__':
    main()
