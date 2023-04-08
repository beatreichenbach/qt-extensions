import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.messagebox import MessageBox


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    MessageBox.warning(QtWidgets.QWidget(), 'Title', 'text')
    MessageBox.question(QtWidgets.QWidget(), 'Title', 'text')
    MessageBox.information(QtWidgets.QWidget(), 'Title', 'text')
    MessageBox.critical(QtWidgets.QWidget(), 'Title', 'text')

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
