import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.icons import MaterialIcon


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    icon = MaterialIcon('folder', MaterialIcon.Style.FILLED)
    button = QtWidgets.QPushButton()
    button.setIcon(icon)
    button.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
