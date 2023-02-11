import logging
import numbers

from PySide2 import QtWidgets, QtGui, QtCore

from qtproperties.widgets import PropertyWidget
from qtproperties.editor import PropertyEditor
from qtproperties import IntProperty, FloatProperty

from flare.qt import utils
from qtmaterialicons.icons import MaterialIcon

# https://pypi.org/project/tabulate/

# move to util?
MAX_INT = (1 << 31) - 1


class TabDataProperty(PropertyWidget):
    # property to display tabular data in qtreewidget
    valueChanged = QtCore.Signal(str)
    accepted_type = list
    # TODO: add support for numpy lists and do proper nested list value validation
    # accepted_type = Union[list, np.array]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_headers(self.headers)
        self.set_types(self.types)

    def init_defaults(self):
        super().init_defaults()
        self.defaults['default'] = []
        self.defaults['headers'] = []
        self.defaults['types'] = []
        self.defaults['decimals'] = 3
        self.defaults['start_index'] = 0

    def init_ui(self):
        # super().init_ui()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # table view
        self.model = QtGui.QStandardItemModel(parent=self)
        self.view = DataTableView(parent=self)
        self.view.setModel(self.model)
        self.view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        palette = self.view.palette()
        palette.setColor(
            QtGui.QPalette.AlternateBase, palette.color(QtGui.QPalette.Window)
        )
        self.view.setPalette(palette)
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

    def connect_ui(self):
        self.model.itemChanged.connect(self.item_changed)

    @property
    def value(self):
        value = []
        for row in range(self.model.rowCount()):
            row_values = []
            for column in range(self.model.columnCount()):
                index = self.model.index(row, column)
                column_value = self.model.data(index, QtCore.Qt.EditRole)
                row_values.append(column_value)
            value.append(row_values)
        return value

    @value.setter
    def value(self, value):
        self.set_data(value)
        self.validate_value(value)
        self.valueChanged.emit(value)

    def set_data(self, data):
        for row, row_data in enumerate(data):
            items = []
            for column, cell_data in enumerate(row_data):
                item = QtGui.QStandardItem()
                item.setData(cell_data, QtCore.Qt.EditRole)
                items.append(item)
            if items:
                self.model.appendRow(items)
        self.update_headers()

    def set_headers(self, headers):
        for i, header in enumerate(headers):
            item = QtGui.QStandardItem()
            item.setText(utils.title(header))
            self.model.setHorizontalHeaderItem(i, item)
        self.resize_headers()

    def set_types(self, types):
        for i, type_ in enumerate(types):
            if issubclass(type_, float):
                self.view.setItemDelegateForColumn(i, FloatDelegate(self))
            elif issubclass(type_, int):
                self.view.setItemDelegateForColumn(i, IntegerDelegate(self))

    def add_row(self):
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
        self.item_changed()
        self.update_headers()

    def remove_row(self):
        self.model.takeRow(self.model.rowCount() - 1)
        self.item_changed()

    def item_changed(self, item=None):
        self.valueChanged.emit(self.value)

    def update_headers(self):
        if self.start_index != 1:
            # horizontal headers
            if not self.headers:
                labels = map(str, range(self.model.columnCount()))
                self.model.setHorizontalHeaderLabels(labels)
                self.resize_headers()

            # vertical headers
            labels = map(str, range(self.model.rowCount()))
            self.model.setVerticalHeaderLabels(labels)

    def resize_headers(self):
        header = self.view.horizontalHeader()
        for i in range(header.count()):
            size = max(self.view.sizeHintForColumn(i), header.sectionSizeHint(i))
            self.view.setColumnWidth(i, size)


class DataTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        # self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)

        self.horizontalHeader().setSortIndicatorShown(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setStretchLastSection(True)

        # header = self.horizontalHeader()
        # header.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )


class IntegerDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def displayText(self, value, locale):
        return str(value)

    def createEditor(self, parent, option, index):
        editor = IntProperty(show_slider=False)
        editor.setParent(parent)
        editor.line.setFrame(False)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        if value:
            editor.value = value

    def setModelData(self, editor, model, index):
        value = editor.value
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class FloatDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

        try:
            self.decimals = parent.decimals
        except AttributeError:
            self.decimals = None

    def displayText(self, value, locale):
        if self.decimals is not None:
            return f'{value:.{self.decimals}f}'.rstrip('0').rstrip('.')
        else:
            return str(value)

    def createEditor(self, parent, option, index):
        editor = FloatProperty(show_slider=False, decimals=6)
        editor.setParent(parent)
        editor.line.setFrame(False)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        if value:
            editor.value = value

    def setModelData(self, editor, model, index):
        value = editor.value
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


def main():
    import sys

    logging.getLogger().setLevel(logging.DEBUG)

    import qtdarkstyle

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()
    editor = PropertyEditor()
    data = [
        ['Sun', 696000, 198],
        ['Earth', 6371, 5973.6],
        ['Moon', 1737, 73.5],
        ['Mars', 3390, 641.85],
        # ['A really big Star', 406320, 339023452345.23450]
    ]
    prop = TabDataProperty(
        name='Data',
        default=data,
        headers=['Name', 'Radius', 'Weight'],
        types=[str, int, float],
    )
    editor.add_property(prop)

    editor.values_changed.connect(logging.debug)
    editor.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
