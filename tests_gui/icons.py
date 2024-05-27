import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.icons import MaterialIcon


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout()
    widget.setLayout(layout)

    icon_names = ('folder', 'cancel', 'search', 'home', 'menu', 'settings')
    for i, style in enumerate(MaterialIcon.Style):
        layout.addWidget(QtWidgets.QLabel(f'{style}'), i, 0)
        for j, name in enumerate(icon_names):
            icon = MaterialIcon(name, style)
            button = QtWidgets.QPushButton()
            button.setIcon(icon)
            layout.addWidget(button, i, j + 1)
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
