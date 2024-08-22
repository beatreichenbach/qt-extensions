import os

from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.elementbrowser import Field
from qt_extensions.filebrowser import FileBrowser


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = FileBrowser(
        os.path.dirname(__file__),
        [Field('name'), Field('path')],
    )
    widget.show()
    return widget


if __name__ == '__main__':
    main()
