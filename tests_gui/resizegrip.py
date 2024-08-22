from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.resizegrip import ResizeGrip


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())
    text = QtWidgets.QPlainTextEdit()
    ResizeGrip(text)
    widget.layout().addWidget(text)
    widget.show()
    return widget


if __name__ == '__main__':
    main()
