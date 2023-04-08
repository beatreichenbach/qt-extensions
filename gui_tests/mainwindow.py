import logging
import sys
from PySide2 import QtWidgets, QtCore

from qt_extensions import theme
from qt_extensions.mainwindow import DockWindow, DockWidget


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    window = DockWindow()
    window.title = 'window'
    window.resize(800, 600)

    window.show()

    floating_windows = []
    for i in range(5):
        dock = DockWidget(window)
        title = f'Panel {i}'
        dock.title = title
        dock.addTab(QtWidgets.QLabel(''), title)
        floating_windows.append(dock)
        dock.setParent(window)
        dock.float()
        dock.show()

    floating_windows[3].add_dock_widget(
        floating_windows[4], QtCore.Qt.RightDockWidgetArea
    )
    window.center_widget.add_dock_widget(
        floating_windows[4], QtCore.Qt.NoDockWidgetArea
    )

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
