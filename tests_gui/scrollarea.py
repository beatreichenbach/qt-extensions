from PySide2 import QtWidgets

from qt_extensions import testing
from qt_extensions.scrollarea import VerticalScrollArea


@testing.gui
def main() -> QtWidgets.QWidget:
    scroll_area = VerticalScrollArea()

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())
    widget.layout().addWidget(QtWidgets.QPushButton('Widget Button'))
    scroll_area.setWidget(widget)

    tab_widget = QtWidgets.QTabWidget()
    tab_widget.addTab(scroll_area, 'Editor')
    tab_widget.show()
    return tab_widget


if __name__ == '__main__':
    main()
