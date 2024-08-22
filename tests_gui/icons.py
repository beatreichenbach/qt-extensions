from PySide2 import QtWidgets, QtCore

from qt_extensions import testing
from qt_extensions.icons import MaterialIcon


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout()
    widget.setLayout(layout)

    size = QtCore.QSize(48, 48)
    icon_names = ('folder', 'cancel', 'search', 'home', 'menu', 'settings')
    for i, style in enumerate(MaterialIcon.Style):
        layout.addWidget(QtWidgets.QLabel(f'{style}'), i, 0)
        for j, name in enumerate(icon_names):
            icon = MaterialIcon(name, style)
            button = QtWidgets.QPushButton()
            button.setIcon(icon)
            button.setIconSize(size)
            layout.addWidget(button, i, j + 1)

        for j, name in enumerate(icon_names):
            icon = MaterialIcon(name, style, fill=True)
            button = QtWidgets.QPushButton()
            button.setIcon(icon)
            button.setIconSize(size)
            layout.addWidget(button, i, len(icon_names) + j + 1)
    widget.show()
    return widget


if __name__ == '__main__':
    main()
