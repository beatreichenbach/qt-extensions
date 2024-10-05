from __future__ import annotations

import enum
from collections.abc import Sequence

from PySide2 import QtWidgets, QtCore, QtGui
from qt_material_icons import MaterialIcon


class CollapsibleBox(QtWidgets.QFrame):
    class Style(enum.Enum):
        NONE = 0
        SIMPLE = 1
        BUTTON = 2

    NONE = Style.NONE
    SIMPLE = Style.SIMPLE
    BUTTON = Style.BUTTON

    def __init__(
        self, title: str = '', parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._maximum_height = self.maximumHeight()
        self._collapsed = False
        self._checkable = False
        self._collapsible = False
        self._style = CollapsibleBox.SIMPLE

        self.title_label = None
        self._expand_label = None
        self._expand_more_icon = MaterialIcon('chevron_right')
        self._expand_less_icon = MaterialIcon('expand_more')
        self._menu_button = None

        self.frame = None
        self.header = None
        self._init_ui()

        if title:
            self.set_title(title)

    def _init_ui(self) -> None:
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum
        )

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setSpacing(0)
        super().setLayout(self._layout)

        # header
        self.header = QtWidgets.QWidget()
        self.header.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.header.installEventFilter(self)
        self.header.setBackgroundRole(QtGui.QPalette.Base)
        self._layout.addWidget(self.header)

        header_layout = QtWidgets.QHBoxLayout()
        self.header.setLayout(header_layout)

        self._expand_label = QtWidgets.QLabel(self.header)
        self._expand_label.setVisible(False)
        header_layout.addWidget(self._expand_label)

        self.checkbox = QtWidgets.QCheckBox(self.header)
        self.checkbox.setVisible(False)
        header_layout.addWidget(self.checkbox)

        self.title_label = QtWidgets.QLabel(self.header)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self._menu_button = QtWidgets.QToolButton(self.header)
        self._menu_button.setIcon(MaterialIcon('menu'))
        self._menu_button.setAutoRaise(True)
        self._menu_button.setVisible(False)
        self._menu_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._menu_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self._menu_button.pressed.connect(self._show_menu)
        size = self.header.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self._menu_button.setMaximumSize(QtCore.QSize(size, size))
        header_layout.addWidget(self._menu_button)

        self._refresh_icon()

        # frame
        self.frame = QtWidgets.QFrame(self)
        self._layout.addWidget(self.frame)
        self._layout.setStretch(1, 1)

        self._refresh_box_style()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.title())})'

    def actionEvent(self, event: QtGui.QActionEvent) -> None:
        self._menu_button.setVisible(bool(self.actions()))
        super().actionEvent(event)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.update()
        super().enterEvent(event)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.header and self._collapsible:
            if (
                event.type() == QtCore.QEvent.MouseButtonPress
                and event.button() == QtCore.Qt.LeftButton
            ):
                self.header.setAutoFillBackground(True)
            if (
                event.type() == QtCore.QEvent.MouseButtonRelease
                and event.button() == QtCore.Qt.LeftButton
            ):
                self.set_collapsed(not self._collapsed)
                self.header.setAutoFillBackground(False)
        return super().eventFilter(watched, event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.update()
        super().leaveEvent(event)

    def layout(self) -> QtWidgets.QLayout:
        return self.frame.layout()

    def setLayout(self, layout: QtWidgets.QLayout) -> None:
        self.frame.setLayout(layout)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        if not self._style == CollapsibleBox.BUTTON:
            return super().paintEvent(event)

        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        if not self._collapsed:
            option.state |= QtWidgets.QStyle.State_Sunken
        if self._collapsed and self.underMouse():
            option.state |= QtWidgets.QStyle.State_MouseOver

        painter = QtGui.QPainter(self)
        style = self.style()
        style.drawPrimitive(
            QtWidgets.QStyle.PE_PanelButtonCommand, option, painter, self
        )

    def setMaximumHeight(self, maxh: int) -> None:
        self._maximum_height = maxh
        super().setMaximumHeight(maxh)

    def setMaximumSize(self, size: QtCore.QSize) -> None:
        self._maximum_height = size.height()
        super().setMaximumSize(size)

    def box_style(self) -> Style:
        return self._style

    def checkable(self) -> bool:
        return self._checkable

    def checked(self) -> bool:
        return self._checkable and self.checkbox.isChecked()

    def collapsible(self) -> bool:
        return self._collapsible

    def collapsed(self) -> bool:
        return self._collapsible and self._collapsed

    def title(self) -> str:
        return self.title_label.text()

    def set_actions(self, actions: Sequence[QtWidgets.QAction]) -> None:
        for action in self.actions():
            self.removeAction(action)
        self.addActions(actions)

    def set_checkable(self, checkable: bool) -> None:
        self._checkable = checkable
        self.checkbox.setVisible(checkable)

    def set_checked(self, checked: bool) -> None:
        if self.checkable():
            self.checkbox.setChecked(checked)

    def set_collapsible(self, collapsible: bool) -> None:
        if collapsible:
            margins = QtCore.QMargins(4, 4, 4, 4)
        else:
            self.set_collapsed(False)
            style = self.header.style()
            left = style.pixelMetric(QtWidgets.QStyle.PM_LayoutLeftMargin)
            top = style.pixelMetric(QtWidgets.QStyle.PM_LayoutTopMargin)
            right = style.pixelMetric(QtWidgets.QStyle.PM_LayoutRightMargin)
            bottom = style.pixelMetric(QtWidgets.QStyle.PM_LayoutBottomMargin)
            margins = QtCore.QMargins(left, top, right, bottom)

        self._collapsible = collapsible
        self.header.layout().setContentsMargins(margins)
        self._expand_label.setVisible(collapsible)

    def set_collapsed(self, collapsed: bool) -> None:
        if self.collapsible():
            self._collapsed = collapsed
            self.frame.setMaximumHeight(0 if collapsed else self._maximum_height)
            self._refresh_icon()

    def set_box_style(self, style: Style) -> None:
        self._style = style
        self._refresh_box_style()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def _refresh_box_style(self) -> None:
        if self._style == CollapsibleBox.Style.SIMPLE:
            self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        else:
            self.setFrameShape(QtWidgets.QFrame.NoFrame)

        if self._style == CollapsibleBox.Style.BUTTON:
            self._layout.setContentsMargins(2, 2, 2, 2)
        else:
            self._layout.setContentsMargins(0, 0, 0, 0)

    def _refresh_icon(self) -> None:
        icon = self._expand_more_icon if self._collapsed else self._expand_less_icon
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_ButtonIconSize)
        self._expand_label.setPixmap(icon.pixmap(size))

    def _show_menu(self) -> None:
        relative_pos = self._menu_button.rect().topRight()
        relative_pos.setX(relative_pos.x() + 2)
        position = self._menu_button.mapToGlobal(relative_pos)

        menu = QtWidgets.QMenu(self)
        menu.addActions(self.actions())
        menu.exec_(position)

        self._menu_button.setDown(False)
