import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.box import CollapsibleBox


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()

    widget.setLayout(QtWidgets.QVBoxLayout())

    group = CollapsibleBox('Settings')
    group.setLayout(QtWidgets.QVBoxLayout())
    group.layout().addWidget(QtWidgets.QPushButton('Button'))

    starburst = CollapsibleBox(
        'Settings', collapsible=True, style=CollapsibleBox.Style.BUTTON
    )
    starburst.setLayout(QtWidgets.QVBoxLayout())
    starburst.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(starburst)

    aperture = CollapsibleBox(
        'Settings', collapsible=True, style=CollapsibleBox.Style.SIMPLE
    )
    aperture.setLayout(QtWidgets.QVBoxLayout())
    aperture.layout().addWidget(QtWidgets.QPushButton('Button'))
    starburst.layout().addWidget(aperture)

    ghost = CollapsibleBox(
        'Settings', collapsible=False, style=CollapsibleBox.Style.SIMPLE
    )
    ghost.setLayout(QtWidgets.QVBoxLayout())
    ghost.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(ghost)

    widget.layout().addWidget(group)

    widget.layout().addStretch()

    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
