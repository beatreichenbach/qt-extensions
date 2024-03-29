from __future__ import annotations

from PySide2 import QtWidgets, QtGui

from qt_extensions.icons import MaterialIcon


class MessageBox(QtWidgets.QMessageBox):
    @staticmethod
    def critical(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok,
        default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
    ) -> QtWidgets.QMessageBox.StandardButton:
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
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok,
        default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
    ) -> QtWidgets.QMessageBox.StandardButton:
        icon = MaterialIcon('info')
        return MessageBox.message(parent, title, text, buttons, default_button, icon)

    @staticmethod
    def question(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Yes
        | QtWidgets.QMessageBox.No,
        default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
    ) -> QtWidgets.QMessageBox.StandardButton:
        icon = MaterialIcon('help')
        return MessageBox.message(parent, title, text, buttons, default_button, icon)

    @staticmethod
    def warning(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok,
        default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
    ) -> QtWidgets.QMessageBox.StandardButton:
        icon = MaterialIcon('warning')
        return MessageBox.message(parent, title, text, buttons, default_button, icon)

    @staticmethod
    def message(
        parent: QtWidgets.QWidget | None,
        title: str,
        text: str,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok,
        default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.NoButton,
        icon: MaterialIcon | None = None,
        color: QtGui.QColor | None = None,
    ) -> QtWidgets.QMessageBox.StandardButton:
        message_box = QtWidgets.QMessageBox(parent)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setStandardButtons(buttons)
        message_box.setDefaultButton(default_button)
        if icon:
            if parent is None:
                parent = QtWidgets.QApplication.instance()
            style = parent.style()
            size = style.pixelMetric(QtWidgets.QStyle.PM_MessageBoxIconSize)
            pixmap = icon.pixmap(size, color=color)
            message_box.setIconPixmap(pixmap)
        return message_box.exec_()
