from PySide2 import QtWidgets, QtGui

from qt_extensions import testing

image = QtGui.QImage()


@testing.gui
def main() -> QtWidgets.QWidget:
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
    return widget


if __name__ == '__main__':
    main()
