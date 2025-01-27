import os

from qt_extensions.elementbrowser import Field
from qt_extensions.filebrowser import FileBrowser
from tests_gui import application


def main() -> None:
    with application():
        widget = FileBrowser(
            os.path.dirname(__file__),
            [Field('name'), Field('path')]
        )
        widget.show()


if __name__ == '__main__':
    main()
