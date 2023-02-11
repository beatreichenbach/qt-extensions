import logging

from PySide2 import QtWidgets, QtCore, QtGui
from qtmaterialicons.icons import MaterialIcon


class CollapsibleHeader(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)
    menu_requested = QtCore.Signal(QtCore.QPoint)

    def __init__(self, title, collapsible=True, parent=None):
        super().__init__(parent)

        self.collapsed = False
        self.title = title
        self.collapsible = collapsible

        self.expand_more_icon = MaterialIcon('expand_more')
        self.expand_less_icon = MaterialIcon('expand_less')

        self.expand_label = None
        self.title_label = None
        self.menu_button = None

        self.init_ui()
        self.update_icon()

    def init_ui(self):

        self.setLayout(QtWidgets.QHBoxLayout(self))
        if self.collapsible:
            self.layout().setContentsMargins(QtCore.QMargins(4, 4, 4, 4))

        self.expand_label = QtWidgets.QLabel(self)
        self.expand_label.setVisible(self.collapsible)
        self.layout().addWidget(self.expand_label)

        self.title_label = QtWidgets.QLabel(self.title, self)
        self.layout().addWidget(self.title_label)
        self.layout().addStretch()

        self.menu_button = QtWidgets.QToolButton(self)
        self.menu_button.setIcon(MaterialIcon('menu'))
        self.menu_button.setAutoRaise(True)
        self.menu_button.setVisible(False)
        self.menu_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.menu_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.menu_button.pressed.connect(self.request_menu)
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self.menu_button.setMaximumSize(QtCore.QSize(size, size))
        self.layout().addWidget(self.menu_button)

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def request_menu(self):
        relative_pos = self.menu_button.rect().topRight()
        relative_pos.setX(relative_pos.x() + 2)
        position = self.menu_button.mapToGlobal(relative_pos)

        self.menu_requested.emit(position)

    def update_icon(self):
        icon = self.expand_more_icon if self.collapsed else self.expand_less_icon
        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_ButtonIconSize)
        self.expand_label.setPixmap(icon.pixmap(size))

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.collapsible:
            self.setAutoFillBackground(True)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:

        if self.collapsible:
            if event.button() == QtCore.Qt.LeftButton:
                self.toggle_collapsed()
            self.setAutoFillBackground(False)

        super().mouseReleaseEvent(event)

    def toggle_collapsed(self):
        self.collapsed = not self.collapsed
        self.update_icon()
        self.toggled.emit(self.collapsed)


class CollapsibleBox(QtWidgets.QFrame):
    SIMPLE = 1
    BUTTON = 2

    def __init__(self, title, collapsible=True, style=None, parent=None):
        super().__init__(parent)

        self._maximum_height = self.maximumHeight()
        self._actions = []

        self.collapsible = collapsible
        self.collapsed = False
        self.frame_style = style

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum
        )

        self._layout = QtWidgets.QVBoxLayout(self)
        super().setLayout(self._layout)
        self._layout.setSpacing(0)

        self.header = CollapsibleHeader(title, collapsible)
        self.header.toggled.connect(self.update_collapsed)
        self.header.menu_requested.connect(self.show_menu)
        self._layout.addWidget(self.header)

        self.frame = QtWidgets.QFrame(self)
        self._layout.addWidget(self.frame)
        self._layout.setStretch(1, 1)

        if self.frame_style == self.SIMPLE:
            self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        if self.frame_style == self.BUTTON:
            self._layout.setContentsMargins(2, 2, 2, 2)
        else:
            self._layout.setContentsMargins(0, 0, 0, 0)

            # TODO: I don't know why setting a color is necessary for the header
            #  to pick that color up, querying the color and brush before and after
            #  gives the same result...
            palette = self.palette()
            palette.setColor(
                QtGui.QPalette.Window, palette.color(QtGui.QPalette.Window)
            )
            self.header.setPalette(palette)

    def update_actions(self, actions):
        self._actions = actions

        # hide menu button if there are no actions
        self.header.menu_button.setVisible(bool(self._actions))

    def show_menu(self, position):
        menu = QtWidgets.QMenu(self)
        menu.addActions(self._actions)

        menu.exec_(position)
        self.header.menu_button.setDown(False)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        if not self.frame_style == self.BUTTON:
            return super().paintEvent(event)

        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        if not self.collapsed or not self.frame_style == self.BUTTON:
            option.state |= QtWidgets.QStyle.State_Sunken
        if self.collapsed and self.underMouse():
            option.state |= QtWidgets.QStyle.State_MouseOver

        style = self.style()
        painter = QtGui.QPainter(self)
        style.drawPrimitive(
            QtWidgets.QStyle.PE_PanelButtonCommand, option, painter, self
        )

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.update()
        super().leaveEvent(event)

    def update_collapsed(self, collapsed):
        self.collapsed = collapsed
        self.frame.setMaximumHeight(0 if collapsed else self._maximum_height)

    def setLayout(self, layout):
        self.frame.setLayout(layout)

    def layout(self):
        return self.frame.layout()


def main():
    import sys

    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    widget = QtWidgets.QWidget()

    widget.setLayout(QtWidgets.QVBoxLayout())

    group = CollapsibleBox('Flare Settings')
    group.setLayout(QtWidgets.QVBoxLayout())
    group.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(QtWidgets.QPushButton('Button'))

    starburst = CollapsibleBox('Starburst Settings', collapsible=True)
    starburst.setLayout(QtWidgets.QVBoxLayout())
    starburst.layout().addWidget(QtWidgets.QPushButton('Button'))
    starburst.layout().addWidget(QtWidgets.QPushButton('Button'))
    starburst.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(starburst)

    ghost = CollapsibleBox(
        'Ghost Settings', collapsible=True, style=CollapsibleBox.SIMPLE
    )
    ghost.setLayout(QtWidgets.QVBoxLayout())
    ghost.layout().addWidget(QtWidgets.QPushButton('Button'))
    ghost.layout().addWidget(QtWidgets.QPushButton('Button'))
    ghost.layout().addWidget(QtWidgets.QPushButton('Button'))
    group.layout().addWidget(ghost)

    widget.layout().addWidget(group)

    widget.layout().addStretch()

    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
