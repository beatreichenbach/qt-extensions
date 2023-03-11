from importlib.resources import files

from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.flexview import FlexView


def flexview():
    import sys
    import logging
    from qt_extensions import theme

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())

    model = QtGui.QStandardItemModel()
    view = FlexView()
    view.setModel(model)
    widget.layout().addWidget(view)

    for i in range(10):
        model.appendRow(QtGui.QStandardItem(f'Item {i}'))

    splash_path = str(files('flare').joinpath('resources').joinpath('splash.png'))
    pixmap = QtGui.QPixmap(splash_path).scaledToWidth(
        200, QtCore.Qt.SmoothTransformation
    )
    for row in range(model.rowCount()):
        model.item(row, 0).setData(pixmap, QtCore.Qt.DecorationRole)

    widget.layout().addWidget(QtWidgets.QLineEdit())
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    flexview()
