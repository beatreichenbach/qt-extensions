from __future__ import annotations

from qt_material_icons import MaterialIcon
from qtpy import QtGui, QtWidgets

StandardButton = QtWidgets.QMessageBox.StandardButton


class MessageBox(QtWidgets.QMessageBox):
    """Message with Material icons, colors and no icons on buttons."""

    def setStandardButtons(
        self, buttons: QtWidgets.QDialogButtonBox.StandardButton
    ) -> None:
        super().setStandardButtons(buttons)
        for button in self.buttons():
            button.setIcon(QtGui.QIcon())

    @staticmethod
    def critical(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: StandardButton = StandardButton.Ok,
        default_button: StandardButton = StandardButton.NoButton,
    ) -> int:
        icon = MaterialIcon('error')
        color = QtGui.QColor('#ff1744')
        return MessageBox.message(
            parent, title, text, buttons, default_button, icon, color
        )

    @staticmethod
    def information(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: StandardButton = StandardButton.Ok,
        default_button: StandardButton = StandardButton.NoButton,
    ) -> int:
        icon = MaterialIcon('info')
        return MessageBox.message(parent, title, text, buttons, default_button, icon)

    @staticmethod
    def question(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: StandardButton = StandardButton.Yes | StandardButton.No,
        default_button: StandardButton = StandardButton.NoButton,
    ) -> int:
        icon = MaterialIcon('help')
        return MessageBox.message(parent, title, text, buttons, default_button, icon)

    @staticmethod
    def warning(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: StandardButton = StandardButton.Ok,
        default_button: StandardButton = StandardButton.NoButton,
    ) -> int:
        icon = MaterialIcon('warning')
        return MessageBox.message(parent, title, text, buttons, default_button, icon)

    @staticmethod
    def message(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: StandardButton = StandardButton.Ok,
        default_button: StandardButton = StandardButton.NoButton,
        icon: MaterialIcon | None = None,
        color: QtGui.QColor | None = None,
    ) -> int:
        message_box = QtWidgets.QMessageBox(parent)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setStandardButtons(buttons)
        message_box.setDefaultButton(default_button)
        if icon:
            if parent is None:
                parent = QtWidgets.QApplication.instance()
            style = parent.style()
            size = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_MessageBoxIconSize)
            pixmap = icon.pixmap(size, color=color)
            message_box.setIconPixmap(pixmap)
        return message_box.exec_()
