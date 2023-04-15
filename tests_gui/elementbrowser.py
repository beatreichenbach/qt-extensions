import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.elementbrowser import ElementBrowser, Field


class Foo:
    pass


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = ElementBrowser([Field('name'), Field('focal')])
    # widget.model.element_added.connect(lambda data: logging.info(data))
    # widget.model.element_removed.connect(lambda data: logging.info(data))
    # widget.model.element_changed.connect(
    #     lambda data, data2: logging.info([data, data2])
    # )
    # widget.model.element_moved.connect(
    #     lambda data, parent: logging.info([data, parent])
    # )

    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
