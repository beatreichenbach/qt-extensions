import logging
import sys

from PySide2 import QtWidgets, QtGui

from qt_extensions import theme
from qt_extensions.scrollarea import VerticalScrollArea


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    scroll_area = VerticalScrollArea()

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())
    widget.layout().addWidget(QtWidgets.QPushButton('Widget Button'))
    scroll_area.setWidget(widget)

    tab_widget = QtWidgets.QTabWidget()
    tab_widget.addTab(scroll_area, 'Editor')
    tab_widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
