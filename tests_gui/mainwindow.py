from qtpy import QtCore, QtWidgets

from qt_extensions.mainwindow import DockWindow, DockWidget
from tests_gui import application


def main() -> None:
    with application():
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
            floating_windows[4], QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        window.center_widget.add_dock_widget(
            floating_windows[4], QtCore.Qt.DockWidgetArea.NoDockWidgetArea
        )


if __name__ == '__main__':
    main()
