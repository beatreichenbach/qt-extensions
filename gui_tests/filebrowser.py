import logging
import os
import sys
from PySide2 import QtWidgets

from qt_extensions.elementbrowser import Field
from qt_extensions.filebrowser import FileBrowser

from qt_extensions import theme


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = FileBrowser(
        os.path.dirname(__file__),
        [Field('name'), Field('path')],
    )
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
