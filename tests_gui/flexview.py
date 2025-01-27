from qtpy import QtGui, QtCore, QtWidgets

from qt_extensions.flexview import FlexView
from tests_gui import application


def main() -> None:
    with application():
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())

        model = QtGui.QStandardItemModel()
        view = FlexView()
        view.grow = True
        view.setModel(model)
        widget.layout().addWidget(view)

        for i in range(10):
            model.appendRow(QtGui.QStandardItem(f'Item {i}'))

        pixmap = QtGui.QPixmap().scaledToWidth(
            200, QtCore.Qt.TransformationMode.SmoothTransformation
        )
        for row in range(model.rowCount()):
            model.item(row, 0).setData(pixmap, QtCore.Qt.ItemDataRole.DecorationRole)

        widget.layout().addWidget(QtWidgets.QLineEdit())
        widget.show()


if __name__ == '__main__':
    main()
