from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions import testing
from qt_extensions.flexview import FlexView


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())

    model = QtGui.QStandardItemModel()
    view = FlexView()
    # view.wrap = FlexView.WrapFlags.NONE
    view.grow = True
    view.setModel(model)
    widget.layout().addWidget(view)

    for i in range(10):
        model.appendRow(QtGui.QStandardItem(f'Item {i}'))

    pixmap = QtGui.QPixmap().scaledToWidth(200, QtCore.Qt.SmoothTransformation)
    for row in range(model.rowCount()):
        model.item(row, 0).setData(pixmap, QtCore.Qt.DecorationRole)

    widget.layout().addWidget(QtWidgets.QLineEdit())
    widget.show()
    return widget


if __name__ == '__main__':
    main()
