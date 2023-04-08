import enum
import logging

from PySide2 import QtWidgets, QtCore, QtGui
from qt_extensions.icons import MaterialIcon


class CollapsibleHeader(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)
    menu_requested = QtCore.Signal(QtCore.QPoint)

    def __init__(
        self, title, collapsible: bool = True, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.title = title

        self._collapsed = False
        self._collapsible = None

        self._expand_more_icon = MaterialIcon('chevron_right')
        self._expand_less_icon = MaterialIcon('expand_more')

        self._expand_label = None
        self._title_label = None
        self.menu_button = None

        self._init_ui()

        self.collapsible = collapsible

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QHBoxLayout())

        self._expand_label = QtWidgets.QLabel(self)
        self.layout().addWidget(self._expand_label)

        self._title_label = QtWidgets.QLabel(self.title, self)
        self.layout().addWidget(self._title_label)
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

        self._update_icon()

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.title)})'

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    @collapsed.setter
    def collapsed(self, value: bool) -> None:
        if value != self._collapsed:
            self._collapsed = value
            self._update_icon()
            self.toggled.emit(self.collapsed)

    @property
    def collapsible(self) -> bool:
        return self._collapsible

    @collapsible.setter
    def collapsible(self, value: bool) -> None:
        self._collapsible = value
        if self.collapsible:
            margins = QtCore.QMargins(4, 4, 4, 4)
        else:
            left = self.style().pixelMetric(QtWidgets.QStyle.PM_LayoutLeftMargin)
            top = self.style().pixelMetric(QtWidgets.QStyle.PM_LayoutTopMargin)
            right = self.style().pixelMetric(QtWidgets.QStyle.PM_LayoutRightMargin)
            bottom = self.style().pixelMetric(QtWidgets.QStyle.PM_LayoutBottomMargin)
            margins = QtCore.QMargins(left, top, right, bottom)

        self.layout().setContentsMargins(margins)
        self._expand_label.setVisible(self.collapsible)

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

    def request_menu(self) -> None:
        relative_pos = self.menu_button.rect().topRight()
        relative_pos.setX(relative_pos.x() + 2)
        position = self.menu_button.mapToGlobal(relative_pos)

        self.menu_requested.emit(position)

    def toggle_collapsed(self) -> None:
        self.collapsed = not self.collapsed

    def _update_icon(self) -> None:
        icon = self._expand_more_icon if self.collapsed else self._expand_less_icon
        style = self.style()
        size = style.pixelMetric(QtWidgets.QStyle.PM_ButtonIconSize)
        self._expand_label.setPixmap(icon.pixmap(size))


class CollapsibleBox(QtWidgets.QFrame):
    class Style(enum.IntFlag):
        NONE = 0
        SIMPLE = enum.auto()
        BUTTON = enum.auto()

    def __init__(
        self,
        title: str,
        collapsible: bool = True,
        style: Style = Style.NONE,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._maximum_height = self.maximumHeight()
        self._actions = []
        self._collapsed = False

        # TODO: make not read-only
        self.title = title
        self.collapsible = collapsible
        self.frame_style = style

        self.header = None
        self.frame = None

        self._init_ui()

    def _init_ui(self) -> None:
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum
        )

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setSpacing(0)
        super().setLayout(self._layout)

        self.header = CollapsibleHeader(self.title, self.collapsible)
        self.header.toggled.connect(self._update_collapsed)
        self.header.menu_requested.connect(self.show_menu)
        self._layout.addWidget(self.header)

        self.frame = QtWidgets.QFrame(self)
        self._layout.addWidget(self.frame)
        self._layout.setStretch(1, 1)

        if self.frame_style == CollapsibleBox.Style.SIMPLE:
            self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        if self.frame_style == CollapsibleBox.Style.BUTTON:
            self._layout.setContentsMargins(2, 2, 2, 2)
        else:
            self._layout.setContentsMargins(0, 0, 0, 0)

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.title)})'

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    @collapsed.setter
    def collapsed(self, value: bool) -> None:
        self.frame.setMaximumHeight(0 if value else self._maximum_height)
        self._collapsed = value
        self.header.blockSignals(True)
        self.header.collapsed = value
        self.header.blockSignals(False)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.update()
        super().leaveEvent(event)

    def layout(self) -> QtWidgets.QLayout:
        return self.frame.layout()

    def setLayout(self, layout: QtWidgets.QLayout) -> None:
        self.frame.setLayout(layout)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        if not self.frame_style == CollapsibleBox.Style.BUTTON:
            return super().paintEvent(event)

        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        if not self.collapsed or not self.frame_style == CollapsibleBox.Style.BUTTON:
            option.state |= QtWidgets.QStyle.State_Sunken
        if self.collapsed and self.underMouse():
            option.state |= QtWidgets.QStyle.State_MouseOver

        style = self.style()
        painter = QtGui.QPainter(self)
        style.drawPrimitive(
            QtWidgets.QStyle.PE_PanelButtonCommand, option, painter, self
        )

    def update_actions(self, actions: list[QtWidgets.QAction]) -> None:
        self._actions = actions

        # hide menu button if there are no actions
        self.header.menu_button.setVisible(bool(self._actions))

    def show_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addActions(self._actions)

        menu.exec_(position)
        self.header.menu_button.setDown(False)

    def _update_collapsed(self, collapsed: bool) -> None:
        self.collapsed = collapsed
