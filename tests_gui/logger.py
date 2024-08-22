import logging

from PySide2 import QtWidgets, QtCore

from qt_extensions import testing
from qt_extensions.logger import LogCache, LogBar

logger = logging.getLogger(__name__)


@testing.gui
def main() -> QtWidgets.QWidget:
    cache = LogCache()
    cache.connect_logger(logging.getLogger())

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

    dialog = QtWidgets.QDialog()
    dialog.resize(QtCore.QSize(800, 100))
    dialog.setLayout(QtWidgets.QVBoxLayout())
    dialog.layout().setContentsMargins(QtCore.QMargins())

    dialog.layout().addStretch()

    status_bar = LogBar(cache)
    dialog.layout().addWidget(status_bar)
    dialog.show()

    status_bar.open_viewer()

    logging.debug('debug')
    logging.error('error')
    logging.info('info')
    logging.critical('critical')
    logging.warning('warning')
    try:
        a = 1 / 0
    except ZeroDivisionError as e:
        logging.exception(e)

    return dialog


if __name__ == '__main__':
    main()
