from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.box import CollapsibleBox


@testing.gui
def main() -> QtWidgets.QWidget:
    widget = QtWidgets.QWidget()

    widget.setLayout(QtWidgets.QVBoxLayout())

    group = CollapsibleBox('Settings')
    group.setLayout(QtWidgets.QVBoxLayout())
    group.addActions([QtWidgets.QAction('Help', group)])
    group.layout().addWidget(QtWidgets.QPushButton('Button'))

    starburst = CollapsibleBox('Settings')
    starburst.set_box_style(CollapsibleBox.BUTTON)
    starburst.set_collapsible(True)
    starburst.setLayout(QtWidgets.QVBoxLayout())
    starburst.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(starburst)

    aperture = CollapsibleBox('Settings')
    aperture.set_box_style(CollapsibleBox.SIMPLE)
    aperture.set_collapsible(True)
    aperture.setLayout(QtWidgets.QVBoxLayout())
    aperture.layout().addWidget(QtWidgets.QPushButton('Button'))
    starburst.layout().addWidget(aperture)

    ghost = CollapsibleBox('Settings')
    ghost.set_box_style(CollapsibleBox.SIMPLE)
    ghost.set_checkable(True)
    ghost.setLayout(QtWidgets.QVBoxLayout())
    ghost.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(ghost)

    widget.layout().addWidget(group)

    widget.layout().addStretch()

    widget.show()
    return widget


if __name__ == '__main__':
    main()
