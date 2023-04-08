import logging
import sys
from PySide2 import QtWidgets

from qt_extensions import theme
from qt_extensions.box import CollapsibleBox
from qt_extensions.button import Button


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()

    widget.setLayout(QtWidgets.QVBoxLayout())

    widget.layout().addWidget(Button('Primary', style=Button.Style.PRIMARY))
    widget.layout().addWidget(Button('None', style=Button.Style.NONE))

    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
