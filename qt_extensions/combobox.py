from PySide2 import QtWidgets, QtGui


class QComboBox(QtWidgets.QComboBox):
    """QComboBox with PlaceholderText support for PySide2."""

    # https://bugreports.qt.io/browse/QTBUG-90595
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        # https://code.qt.io/cgit/qt/qtbase.git/tree/src/widgets/widgets/qcombobox.cpp#n2975
        painter = QtWidgets.QStylePainter(self)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))

        # draw the combobox frame, focusrect and selected etc.
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)

        if self.currentIndex() < 0:
            opt.palette.setBrush(
                QtGui.QPalette.ButtonText,
                opt.palette.brush(QtGui.QPalette.ButtonText).color(),
            )
            if self.placeholderText():
                opt.currentText = self.placeholderText()

        # draw the icon and text
        painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt)
