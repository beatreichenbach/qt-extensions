import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.resizegrip import ResizeGrip


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())
    text = QtWidgets.QPlainTextEdit()
    ResizeGrip(text)
    widget.layout().addWidget(text)
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
