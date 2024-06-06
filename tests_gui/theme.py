import logging
import sys

from PySide2 import QtWidgets, QtGui

from qt_extensions import theme

image = QtGui.QImage()


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    theme.apply_theme(theme.monokai)

    widget = QtWidgets.QWidget()
    widget.setMinimumWidth(400)
    widget.setLayout(QtWidgets.QVBoxLayout())

    palette = widget.palette()

    roles = [r for r in vars(QtGui.QPalette.ColorRole).keys() if r[0].isupper()]
    for name in roles:
        # role
        role = getattr(QtGui.QPalette.ColorRole, name)

        if role in (
            QtGui.QPalette.ColorRole.NoRole,
            QtGui.QPalette.ColorRole.NColorRoles,
        ):
            continue

        # frame
        frame = QtWidgets.QFrame()
        frame.setBackgroundRole(role)

        frame.setAutoFillBackground(True)
        frame.setLayout(QtWidgets.QHBoxLayout())
        widget.layout().addWidget(frame)

        # label
        label = QtWidgets.QLabel(name)
        rgb = palette.color(role).getRgbF()
        color = QtGui.QColor.fromRgbF(1 - rgb[0], 1 - rgb[1], 1 - rgb[2])
        palette.setColor(QtGui.QPalette.WindowText, color)
        label.setPalette(palette)
        frame.layout().addWidget(label)

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
