import sys
from PySide2 import QtWidgets, QtGui


def get_palette():
    # Original color palette from https://github.com/gmarull/qtmodern

    palette = QtGui.QPalette()

    # colors
    primary = QtGui.QColor(42, 130, 218)
    secondary = QtGui.QColor(56, 252, 196)
    black1 = QtGui.QColor(20, 20, 20)
    dark1 = QtGui.QColor(35, 35, 35)
    dark2 = QtGui.QColor(42, 42, 42)
    dark3 = QtGui.QColor(53, 53, 53)
    medium1 = QtGui.QColor(66, 66, 66)
    medium2 = QtGui.QColor(80, 80, 80)
    medium3 = QtGui.QColor(90, 90, 90)
    bright1 = QtGui.QColor(127, 127, 127)
    bright2 = QtGui.QColor(180, 180, 180)

    # base
    palette.setColor(QtGui.QPalette.WindowText, bright2)
    palette.setColor(QtGui.QPalette.Button, dark3)
    palette.setColor(QtGui.QPalette.Light, bright2)
    palette.setColor(QtGui.QPalette.Midlight, medium3)
    palette.setColor(QtGui.QPalette.Dark, dark1)
    palette.setColor(QtGui.QPalette.Text, bright2)
    palette.setColor(QtGui.QPalette.BrightText, bright2)
    palette.setColor(QtGui.QPalette.ButtonText, bright2)
    palette.setColor(QtGui.QPalette.Base, dark2)
    palette.setColor(QtGui.QPalette.Window, dark3)
    palette.setColor(QtGui.QPalette.Shadow, black1)
    palette.setColor(QtGui.QPalette.Highlight, primary)
    palette.setColor(QtGui.QPalette.HighlightedText, bright2)
    palette.setColor(QtGui.QPalette.Link, secondary)
    palette.setColor(QtGui.QPalette.AlternateBase, medium1)
    palette.setColor(QtGui.QPalette.ToolTipBase, dark3)
    palette.setColor(QtGui.QPalette.ToolTipText, bright2)
    palette.setColor(QtGui.QPalette.LinkVisited, medium2)

    # disabled
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, bright1)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, bright1)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, bright1)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, medium2)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, bright1)

    return palette


def apply_style(app: QtWidgets.QApplication = None) -> None:
    # app
    if app is None:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    palette = get_palette()

    app.setPalette(palette)
    app.setStyle('Fusion')

    # QScrollArea background color fix
    scrollarea_palette = QtGui.QPalette(palette)
    scrollarea_palette.setColor(
        QtGui.QPalette.Window, palette.color(QtGui.QPalette.AlternateBase)
    )
    app.setPalette(scrollarea_palette, QtWidgets.QScrollArea.__name__)

    # QTabWidget background tab fix
    tab_widget_palette = QtGui.QPalette(palette)
    tab_widget_palette.setColor(
        QtGui.QPalette.Light, palette.color(QtGui.QPalette.Midlight)
    )
    app.setPalette(tab_widget_palette, QtWidgets.QTabWidget.__name__)
