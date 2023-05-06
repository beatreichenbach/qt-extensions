import re
from functools import partial

from qt_extensions import theme
from qt_extensions.button import CheckBoxButton
from qt_extensions.icons import MaterialIcon

import logging
from PySide2 import QtWidgets, QtCore, QtGui


class Sender(QtCore.QObject):
    signal = QtCore.Signal(object)


class Handler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)

        self._sender = Sender()
        self.record_logged = self._sender.signal

    def emit(self, record: logging.LogRecord) -> None:
        self.record_logged.emit(record)


class LogCache(QtCore.QObject):
    added: QtCore.Signal = QtCore.Signal(logging.LogRecord)
    cleared: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)

        self.records = []
        self.handler = Handler()
        self.handler.record_logged.connect(self.add)

    def add(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        self.added.emit(record)

    def clear(self) -> None:
        self.records = []
        self.cleared.emit()

    def connect_logger(self, logger: logging.Logger) -> None:
        logger.addHandler(self.handler)


class LogViewer(QtWidgets.QWidget):
    def __init__(
        self, cache: LogCache, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.cache = cache
        self.cache.added.connect(self.add_record)
        self.cache.cleared.connect(self.clear)
        self.levels = {
            logging.ERROR: True,
            logging.WARNING: True,
            logging.INFO: True,
            logging.DEBUG: True,
        }

        self._init_ui()

        color = self.palette().color(QtGui.QPalette.Text).name()
        self.formatter = logging.Formatter(
            fmt='[{asctime}]<font color="{color}"><b>[{levelname: <8}]</b></font> {message}',
            datefmt='%I:%M:%S%p',
            style='{',
            defaults={'color': color},
        )

        self._error_color = theme.Color('error').name()
        self._warning_color = theme.Color('warning').name()
        self._info_color = theme.Color('info').name()

        self._error_count = 0
        self._warning_count = 0

        for record in self.cache.records:
            self.add_record(record)

    def _init_ui(self) -> None:
        self.setWindowTitle('Log Viewer')

        self.setLayout(QtWidgets.QVBoxLayout())

        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setReadOnly(True)

        font = QtGui.QFont('Monospace')
        font.setStyleHint(QtGui.QFont.Monospace)
        self.text_edit.setFont(font)

        self.layout().addWidget(self.text_edit)

        # toolbar
        self.toolbar = QtWidgets.QToolBar()
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self.toolbar.setIconSize(QtCore.QSize(size, size))
        self.layout().insertWidget(0, self.toolbar)

        # level buttons
        button = CheckBoxButton('Error', color='error')
        button.setFlat(True)
        button.setChecked(True)
        button.toggled.connect(partial(self._level_toggle, logging.ERROR))
        self.toolbar.addWidget(button)
        self._error_button = button

        button = CheckBoxButton('Warning', color='warning')
        button.setFlat(True)
        button.setChecked(True)
        button.toggled.connect(partial(self._level_toggle, logging.WARNING))
        self.toolbar.addWidget(button)
        self._warning_button = button

        button = CheckBoxButton('Info', color='info')
        button.setFlat(True)
        button.setChecked(True)
        button.toggled.connect(partial(self._level_toggle, logging.INFO))
        self.toolbar.addWidget(button)

        button = CheckBoxButton('Debug', color='info')
        button.setFlat(True)
        button.setChecked(True)
        button.toggled.connect(partial(self._level_toggle, logging.DEBUG))
        self.toolbar.addWidget(button)

        # stretch
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.toolbar.addWidget(spacer)

        # actions
        action = QtWidgets.QAction(self)
        action.setText('Wrap Lines')
        action.setCheckable(True)
        action.setChecked(True)
        icon = MaterialIcon('wrap_text')
        action.setIcon(icon)
        action.toggled.connect(self._wrap_text)
        self.toolbar.addAction(action)

        action = QtWidgets.QAction(self)
        action.setText('Clear')
        icon = MaterialIcon('backspace')
        action.setIcon(icon)
        action.triggered.connect(self.cache.clear)
        self.toolbar.addAction(action)

    @property
    def error_count(self) -> int:
        return self._error_count

    @error_count.setter
    def error_count(self, value: int) -> None:
        self._error_count = value
        self._error_button.setText(f'Error: {value}')

    @property
    def warning_count(self) -> int:
        return self._warning_count

    @warning_count.setter
    def warning_count(self, value: int) -> None:
        self._warning_count = value
        self._warning_button.setText(f'Warning: {value}')

    def clear(self) -> None:
        self.text_edit.clear()
        self.error_count = 0
        self.warning_count = 0

    def add_record(self, record: logging.LogRecord, count: bool = True):
        if record.levelno >= logging.ERROR:
            if count:
                self.error_count += 1
            if not self.levels[logging.ERROR]:
                return
            record.color = self._error_color
        elif record.levelno >= logging.WARNING:
            if count:
                self.warning_count += 1
            if not self.levels[logging.WARNING]:
                return
            record.color = self._warning_color
        elif record.levelno >= logging.INFO:
            if not self.levels[logging.INFO]:
                return
            record.color = self._info_color
        elif record.levelno >= logging.DEBUG:
            if not self.levels[logging.DEBUG]:
                return
            record.color = self._info_color
        else:
            return

        text = self.formatter.format(record)
        for match in re.findall(r'>.*?</', text):
            html = match.replace(' ', '&nbsp;')
            text = text.replace(match, html)
        self.text_edit.appendHtml(text)

    def _filter(self):
        self.text_edit.clear()
        for record in self.cache.records:
            self.add_record(record, count=False)

    def _level_toggle(self, level: int, checked: bool) -> None:
        self.levels[level] = checked
        self._filter()

    def _wrap_text(self, checked: bool) -> None:
        if checked:
            self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        else:
            self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            self.text_edit.horizontalScrollBar().setValue(0)


class LogBar(QtWidgets.QWidget):
    def __init__(
        self, cache: LogCache, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.cache = cache
        self.current_message = logging.makeLogRecord({'levelno': 0})
        self._viewer = None

        self.formatter = logging.Formatter(fmt='[{levelname}] {message}', style='{')

        self._init_ui()

        self.cache.added.connect(
            lambda record: self.show_message(
                self.formatter.format(record), level=record.levelno
            )
        )
        self.cache.cleared.connect(lambda: self.show_message('', force=True))

    def _init_ui(self):
        # colors
        self._critical_color = theme.Color('critical')
        self._error_color = theme.Color('error')
        self._warning_color = theme.Color('warning')

        # log icons
        self.log_icons = {
            logging.CRITICAL: MaterialIcon('report'),
            logging.ERROR: MaterialIcon('error'),
            logging.WARNING: MaterialIcon('warning'),
            logging.INFO: MaterialIcon('article'),
        }
        self.log_icons[logging.CRITICAL].set_color(self._critical_color)
        self.log_icons[logging.ERROR].set_color(self._error_color)
        self.log_icons[logging.WARNING].set_color(self._warning_color)

        # layout
        size_policy = self.sizePolicy()
        size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Maximum)
        self.setSizePolicy(size_policy)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(QtCore.QMargins())

        # message
        message_layout = QtWidgets.QHBoxLayout()
        message_layout.setContentsMargins(QtCore.QMargins())
        message_layout.setSpacing(0)

        # message button
        self.log_button = QtWidgets.QToolButton(self)
        self.log_button.setIcon(self.log_icons[logging.INFO])
        self.log_button.setAutoRaise(True)
        self.log_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.log_button.pressed.connect(self.open_viewer)

        message_layout.addWidget(self.log_button)

        # message line
        self.message_line = QtWidgets.QLineEdit()
        self.message_line.setReadOnly(True)
        self.message_line.setFocusPolicy(QtCore.Qt.NoFocus)

        font = QtGui.QFont('Roboto Mono')
        font.setStyleHint(QtGui.QFont.Monospace)
        self.message_line.setFont(font)
        message_layout.addWidget(self.message_line)

        layout.addLayout(message_layout)
        layout.setStretch(0, 1)

        # size grip
        size_grip = QtWidgets.QSizeGrip(self)
        layout.addWidget(size_grip, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

    def add_widget(self, widget: QtWidgets.QWidget):
        count = self.layout().count()
        self.layout().insertWidget(count - 1, widget)

    def remove_widget(self, widget: QtWidgets.QWidget):
        self.layout().removeWidget(widget)

    def clear_message(self):
        self.show_message('', force=True)

    def show_message(self, message: str, level: int = logging.INFO, force=False):
        if not force and level < self.current_message.levelno:
            return

        self.message_line.setText(message)

        if level >= logging.CRITICAL:
            self.log_button.setIcon(self.log_icons[logging.CRITICAL])
            color = self._critical_color
        elif level >= logging.ERROR:
            self.log_button.setIcon(self.log_icons[logging.ERROR])
            color = self._error_color
        elif level >= logging.WARNING:
            self.log_button.setIcon(self.log_icons[logging.WARNING])
            color = self._warning_color
        else:
            self.log_button.setIcon(self.log_icons[logging.INFO])
            color = self.palette().color(QtGui.QPalette.Window)

        palette = self.message_line.palette()
        palette.setColor(QtGui.QPalette.Window, color)
        self.message_line.setPalette(palette)

        self.current_message = logging.makeLogRecord({'msg': message, 'levelno': level})

    def open_viewer(self):
        if self._viewer is None:
            self._viewer = LogViewer(self.cache)
        self._viewer.show()
