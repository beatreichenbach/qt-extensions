import sys

from qt_extensions import theme

import logging
from PySide2 import QtWidgets, QtCore, QtGui

from qt_extensions.logger import LogCache, LogBar, LogViewer
from qt_extensions.mainwindow import DockWidget, DockWindow

logger = logging.getLogger(__name__)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.modern_dark)

    cache = LogCache()
    cache.connect_logger(logging.getLogger())

    # logging.getLogger().addHandler(logging.StreamHandler())

    for i in range(100):
        logger.debug('debug')
        logger.error('error')
        logger.info('info')
        logger.critical('critical')
        logger.warning('warning')

    logger2 = logging.getLogger('qt_extensions')
    cache.connect_logger(logger2)
    for i in range(20):
        logger2.debug('debug')
        logger2.error('error')
        logger2.info('info')
        logger2.critical('critical')
        logger2.warning('warning')

    # dialog = QtWidgets.QDialog()
    # dialog.resize(QtCore.QSize(800, 100))
    # dialog.setLayout(QtWidgets.QVBoxLayout())
    # dialog.layout().setContentsMargins(QtCore.QMargins())
    #
    # button = QtWidgets.QPushButton('Error')
    # button.pressed.connect(lambda: logger.error('This is an Error message'))
    # dialog.layout().addWidget(button)
    #
    # button = QtWidgets.QPushButton('Warning')
    # button.pressed.connect(lambda: logger.warning('This is an Warning message'))
    # dialog.layout().addWidget(button)
    #
    # button = QtWidgets.QPushButton('Info')
    # button.pressed.connect(lambda: logger.info('This is an Info message'))
    # dialog.layout().addWidget(button)
    #
    # button = QtWidgets.QPushButton('Exception')
    # button.pressed.connect(
    #     lambda: logger.exception(Exception('This is an Exception message'))
    # )
    # dialog.layout().addWidget(button)
    #
    # dialog.layout().addStretch()
    #
    # status_bar = LogBar(cache)
    # dialog.layout().addWidget(status_bar)
    # dialog.show()
    #
    # status_bar.open_viewer()

    viewer = LogViewer()
    viewer.set_cache(cache)
    window = DockWindow()
    dock_widget = DockWidget(dock_window=window)
    dock_widget.addTab(viewer, 'Status_Bar')
    window.show()

    logging.debug('debug')
    logging.error('error')
    logging.info('info')
    logging.critical('critical')
    logging.warning('warning')
    try:
        a = 1 / 0
    except ZeroDivisionError as e:
        logging.exception(e)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
