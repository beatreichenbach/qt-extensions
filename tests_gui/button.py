from PySide2 import QtWidgets, QtGui

from qt_extensions import testing
from qt_extensions.button import Button, CheckBoxButton


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = QtWidgets.QWidget()

    widget.setLayout(QtWidgets.QHBoxLayout())

    button = Button('Yes', color='primary')
    widget.layout().addWidget(button)

    button = Button('No')
    widget.layout().addWidget(button)

    button = Button('Disabled', color='primary')
    button.setEnabled(False)
    widget.layout().addWidget(button)

    button = CheckBoxButton('Warning: 10', color='warning')
    widget.layout().addWidget(button)

    button = CheckBoxButton('Error: 2', color='error')
    button.setChecked(True)
    widget.layout().addWidget(button)

    button = CheckBoxButton('Debug: 0', color='info')
    button.setFlat(True)
    widget.layout().addWidget(button)

    button = Button('Custom Color')
    button.set_color(QtGui.QColor(20, 200, 220))
    widget.layout().addWidget(button)

    button = CheckBoxButton('Debug: 0', color='info')
    button.setChecked(True)
    button.setEnabled(False)
    widget.layout().addWidget(button)

    widget.show()
    return widget


if __name__ == '__main__':
    main()
