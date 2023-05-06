import sys

from qt_extensions import theme

import logging
from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.logger import LogCache, LogBar


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    cache = LogCache()
    cache.connect_logger(logging.getLogger())

    for i in range(100):
        logging.debug('debug')
        logging.error('error')
        logging.info('info')
        logging.critical('critical')
        logging.warning('warning')

    dialog = QtWidgets.QDialog()
    dialog.resize(QtCore.QSize(800, 100))
    dialog.setLayout(QtWidgets.QVBoxLayout())
    dialog.layout().setContentsMargins(QtCore.QMargins())

    button = QtWidgets.QPushButton('Error')
    button.pressed.connect(lambda: logging.error('This is an Error message'))
    dialog.layout().addWidget(button)

    button = QtWidgets.QPushButton('Warning')
    button.pressed.connect(lambda: logging.warning('This is an Warning message'))
    dialog.layout().addWidget(button)

    button = QtWidgets.QPushButton('Info')
    button.pressed.connect(lambda: logging.info('This is an Info message'))
    dialog.layout().addWidget(button)

    button = QtWidgets.QPushButton('Exception')
    button.pressed.connect(
        lambda: logging.exception(Exception('This is an Exception message'))
    )
    dialog.layout().addWidget(button)

    dialog.layout().addStretch()

    status_bar = LogBar(cache)
    dialog.layout().addWidget(status_bar)
    dialog.show()

    logging.debug('debug')
    logging.error('error')
    logging.info('info')
    logging.critical('critical')
    logging.warning('warning')

    # viewer = LogViewer(cache)
    # viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
