from __future__ import annotations

import html
import logging
import os
from collections.abc import Sequence
from functools import partial

from PySide2 import QtWidgets, QtCore, QtGui
from qt_material_icons import MaterialIcon

from qt_extensions import theme
from qt_extensions.button import CheckBoxButton

SUCCESS = 25

logging.addLevelName(SUCCESS, 'SUCCESS')


class LogCache(QtCore.QObject):
    added: QtCore.Signal = QtCore.Signal(logging.LogRecord)
    cleared: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)

        self.records = []
        self.handler = logging.Handler()
        self.handler.emit = self.add
        self.destroyed.connect(self.cleanup)

    def add(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        self.added.emit(record)

    def clear(self) -> None:
        self.records = []
        self.cleared.emit()

    def connect_logger(self, logger: logging.Logger) -> None:
        logger.addHandler(self.handler)

    def save(self, filename: str) -> None:
        formatter = logging.Formatter(
            fmt='[{asctime}][{levelname: <8}][{name}] {message}',
            datefmt='%I:%M:%S%p',
            style='{',
        )

        with open(filename, 'w') as f:
            text = (f'{formatter.format(record)}\n' for record in self.records)
            f.writelines(text)

    def cleanup(self) -> None:
        self.handler.emit = logging.Handler.emit
        self.handler.close()


class LogViewer(QtWidgets.QWidget):
    def __init__(
        self, cache: LogCache | None = None, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._cache = None
        self._cache_connected = False
        self._error_color = theme.Color('error').name()
        self._warning_color = theme.Color('warning').name()
        self._success_color = theme.Color('success').name()
        self._error_count = 0
        self._warning_count = 0
        self._last_save_path = os.path.expanduser('~')
        self._names = set()
        self._levels = set()

        # To escape html later, use placeholders.
        fmt = '[{asctime}][html][{levelname: <8}][/html] {message}'
        self.formatter = logging.Formatter(
            fmt=fmt,
            datefmt='%I:%M:%S%p',
            style='{',
        )
        self._init_ui()

        self.set_levels((logging.ERROR, logging.WARNING))

        if cache:
            self.set_cache(cache)

    def _init_ui(self) -> None:
        self.setWindowTitle('Log Viewer')

        self.setLayout(QtWidgets.QVBoxLayout())

        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        font = QtGui.QFont()
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
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.toggled.connect(partial(self._level_toggle, logging.ERROR))
        self.toolbar.addWidget(button)
        self._error_button = button

        button = CheckBoxButton('Warning', color='warning')
        button.setFlat(True)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.toggled.connect(partial(self._level_toggle, logging.WARNING))
        self.toolbar.addWidget(button)
        self._warning_button = button

        button = CheckBoxButton('Info')
        button.setFlat(True)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.toggled.connect(partial(self._level_toggle, logging.INFO))
        self.toolbar.addWidget(button)
        self._info_button = button

        button = CheckBoxButton('Debug')
        button.setFlat(True)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.toggled.connect(partial(self._level_toggle, logging.DEBUG))
        self.toolbar.addWidget(button)
        self._debug_button = button

        # stretch
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.toolbar.addWidget(spacer)

        # actions
        action = QtWidgets.QAction(self)
        action.setText('Filter')
        icon = MaterialIcon('filter_alt')
        action.setIcon(icon)
        action.triggered.connect(self._show_filter_menu)
        self.toolbar.addAction(action)
        self._filter_action = action

        action = QtWidgets.QAction(self)
        action.setText('Wrap Lines')
        action.setCheckable(True)
        icon = MaterialIcon('wrap_text')
        action.setIcon(icon)
        action.toggled.connect(self._wrap_text)
        self.toolbar.addAction(action)
        self._wrap_action = action

        action = QtWidgets.QAction(self)
        action.setText('Save')
        icon = MaterialIcon('save')
        action.setIcon(icon)
        action.triggered.connect(self.save)
        self.toolbar.addAction(action)

        action = QtWidgets.QAction(self)
        action.setText('Clear')
        icon = MaterialIcon('backspace')
        action.setIcon(icon)
        self.toolbar.addAction(action)
        self._clear_action = action

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

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._disconnect_cache()
        super().closeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._connect_cache()
        super().showEvent(event)
        self.refresh()

    def add_name(self, name: str, add: bool = True) -> None:
        if add:
            self._names.add(name)
        else:
            try:
                self._names.remove(name)
            except KeyError:
                pass
        self.refresh()

    def add_record(self, record: logging.LogRecord, count: bool = True) -> None:
        if self._names and not record.name.startswith(tuple(self._names)):
            return

        # NOTE: python 3.9 does not allow defaults in the formatter
        record.color = ''

        if record.levelno >= logging.ERROR:
            if count:
                self.error_count += 1
            if self._levels and logging.ERROR not in self._levels:
                return
            record.color = self._error_color
        elif record.levelno >= logging.WARNING:
            if count:
                self.warning_count += 1
            if self._levels and logging.WARNING not in self._levels:
                return
            record.color = self._warning_color
        elif record.levelno == SUCCESS:
            if self._levels and logging.INFO not in self._levels:
                return
            record.color = self._success_color
        elif record.levelno >= logging.INFO:
            if self._levels and logging.INFO not in self._levels:
                return
        elif record.levelno >= logging.DEBUG:
            if self._levels and logging.DEBUG not in self._levels:
                return
        else:
            return

        message = self.formatter.format(record)
        message = html.escape(message, quote=False)
        message = message.replace(
            '[html]',
            f'<font color="{record.color}"><b>',
        )
        message = message.replace('[/html]', '</b></font>')

        if record.exc_info:
            lines = message.split('\n')
            try:
                header = lines.pop(0)
                trace = '\n'.join(lines)
                message = f'{header}\n<font color="{self._error_color}">{trace}</font>'
            except IndexError:
                pass
        inner_html = f'<pre><code data-lang="python">{message}</code></pre>'

        self.text_edit.appendHtml(inner_html)

    def cache(self) -> LogCache | None:
        return self._cache

    def clear(self) -> None:
        self.text_edit.clear()
        self.error_count = 0
        self.warning_count = 0

    def refresh(self) -> None:
        self.clear()
        if self._cache:
            for record in self._cache.records:
                self.add_record(record)

    def save(self) -> None:
        if not self._cache:
            return
        filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save File',
            dir=self._last_save_path,
            filter='*.log',
        )

        if filename:
            path = os.path.dirname(filename)
            self._last_save_path = path
            if not os.path.exists(path):
                os.makedirs(path)
            self._cache.save(filename)

    def set_cache(self, cache: LogCache) -> None:
        self._disconnect_cache()
        self._cache = cache
        self._clear_action.triggered.connect(self._cache.clear)
        if self.isVisible():
            self._connect_cache()

    def set_levels(self, levels: Sequence[int]) -> None:
        self._levels = set(levels)
        self._error_button.setChecked(logging.ERROR in self._levels)
        self._warning_button.setChecked(logging.WARNING in self._levels)
        self._info_button.setChecked(logging.INFO in self._levels)
        self._debug_button.setChecked(logging.DEBUG in self._levels)

    def set_names(self, names: Sequence[str]) -> None:
        self._names = set(names)
        self.refresh()

    def set_state(self, state: dict) -> None:
        values = {
            'names': set(),
            'levels': {logging.ERROR, logging.WARNING, logging.INFO},
            'wrap': False,
        }
        values.update(state)

        self.set_levels(tuple(values['levels']))
        self.set_names(tuple(values['names']))
        self._wrap_action.setChecked(values['wrap'])

    def state(self) -> dict:
        log_viewer_state = {
            'names': self._names,
            'levels': self._levels,
            'wrap': self._wrap_action.isChecked(),
        }
        return log_viewer_state

    def _connect_cache(self) -> None:
        if self._cache and not self._cache_connected:
            self._cache.added.connect(self.add_record)
            self._cache.cleared.connect(self.clear)
            self._cache_connected = True

    def _disconnect_cache(self) -> None:
        if self._cache:
            try:
                self._cache.added.disconnect(self.add_record)
                self._cache.cleared.disconnect(self.clear)
            except RuntimeError:
                pass
            self._cache_connected = False
            self.clear()

    def _filter(self) -> None:
        self.text_edit.clear()
        if self._cache:
            for record in self._cache.records:
                self.add_record(record, count=False)

    def _level_toggle(self, level: int, checked: bool) -> None:
        if checked:
            self._levels.add(level)
        else:
            try:
                self._levels.remove(level)
            except KeyError:
                pass
        self._filter()

    def _show_filter_menu(self) -> None:
        if not self._cache:
            return
        widget = self.toolbar.widgetForAction(self._filter_action)
        relative_pos = widget.rect().topRight()
        relative_pos.setX(relative_pos.x() + 2)
        position = widget.mapToGlobal(relative_pos)

        names = set()
        for record in self._cache.records:
            name = record.name.split('.')[0]
            names.add(name)

        for name in self._names:
            names.add(name)

        menu = QtWidgets.QMenu(self)
        for name in names:
            action = QtWidgets.QAction(self)
            action.setText(name)
            action.setCheckable(True)
            action.toggled.connect(partial(self.add_name, name))
            menu.addAction(action)

            if name in self._names:
                action.setChecked(True)
        menu.exec_(position)

    def _wrap_text(self, checked: bool) -> None:
        if checked:
            self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        else:
            self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            self.text_edit.horizontalScrollBar().setValue(0)


class LogBar(QtWidgets.QWidget):
    def __init__(
        self, cache: LogCache | None = None, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._cache = None
        self._viewer = None

        self.current_message = logging.makeLogRecord({'levelno': logging.NOTSET})
        self.formatter = logging.Formatter(fmt='[{levelname}] {message}', style='{')
        self.level = SUCCESS
        self.names = set()

        self._init_ui()

        if not cache:
            cache = LogCache(self)
            cache.connect_logger(logging.getLogger())
        self.set_cache(cache)

    def _init_ui(self) -> None:
        # colors
        self._critical_color = theme.Color('critical')
        self._error_color = theme.Color('error')
        self._warning_color = theme.Color('warning')
        self._success_color = theme.Color('success')

        # log icons
        self._critical_icon = MaterialIcon('report')
        self._critical_icon.set_color(self._critical_color)
        self._error_icon = MaterialIcon('error')
        self._error_icon.set_color(self._error_color)
        self._warning_icon = MaterialIcon('warning')
        self._warning_icon.set_color(self._warning_color)
        self._info_icon = MaterialIcon('article')
        self._success_icon = MaterialIcon('check_circle')
        self._success_icon.set_color(self._success_color)

        # layout
        size_policy = self.sizePolicy()
        size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Maximum)
        self.setSizePolicy(size_policy)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(QtCore.QMargins())

        # message
        message_layout = QtWidgets.QHBoxLayout()
        message_layout.setContentsMargins(2, 2, 2, 2)
        message_layout.setSpacing(0)

        # message button
        self.log_button = QtWidgets.QToolButton(self)
        self.log_button.setIcon(self._info_icon)
        self.log_button.setAutoRaise(True)
        self.log_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.log_button.clicked.connect(self.open_viewer)

        message_layout.addWidget(self.log_button)

        # message line
        self.message_line = QtWidgets.QLineEdit(self)
        self.message_line.setReadOnly(True)
        self.message_line.setFocusPolicy(QtCore.Qt.NoFocus)

        font = QtGui.QFont()
        font.setStyleHint(QtGui.QFont.Monospace)
        self.message_line.setFont(font)
        message_layout.addWidget(self.message_line)

        layout.addLayout(message_layout)
        layout.setStretch(0, 1)

        # size grip
        self.size_grip = QtWidgets.QSizeGrip(self)
        layout.addWidget(
            self.size_grip, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight
        )

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        count = self.layout().count()
        self.layout().insertWidget(count - 1, widget)

    def cache(self) -> LogCache | None:
        return self._cache

    def clear_message(self) -> None:
        self.show_message('', level=logging.NOTSET, force=True)

    def open_viewer(self) -> None:
        if self._viewer is None:
            self._viewer = LogViewer(self._cache, parent=self)
            self._viewer.setWindowFlag(QtCore.Qt.Dialog)
            self._viewer.resize(QtCore.QSize(720, 480))
        self._viewer.show()

    def remove_widget(self, widget: QtWidgets.QWidget) -> None:
        self.layout().removeWidget(widget)

    def set_cache(self, cache: LogCache) -> None:
        self._cache = cache
        self._cache.added.connect(self.show_record)
        self._cache.cleared.connect(self.clear_message)

    def show_message(
        self, message: str, level: int = logging.INFO, force=False
    ) -> None:
        if not force:
            if level < self.current_message.levelno or level < self.level:
                return

        if level == SUCCESS:
            self.log_button.setIcon(self._success_icon)
            color = self._success_color
        elif level >= logging.CRITICAL:
            self.log_button.setIcon(self._critical_icon)
            color = self._critical_color
        elif level >= logging.ERROR:
            self.log_button.setIcon(self._error_icon)
            color = self._error_color
        elif level >= logging.WARNING:
            self.log_button.setIcon(self._warning_icon)
            color = self._warning_color
        else:
            self.log_button.setIcon(self._info_icon)
            color = self.palette().color(QtGui.QPalette.Window)

        self.message_line.setText(message)
        self.message_line.setCursorPosition(0)
        palette = self.message_line.palette()
        palette.setColor(QtGui.QPalette.Window, color)
        self.message_line.setPalette(palette)

        self.current_message = logging.makeLogRecord({'msg': message, 'levelno': level})

    def show_record(self, record: logging.LogRecord) -> None:
        if record is None or (
            self.names and not record.name.startswith(tuple(self.names))
        ):
            return
        message = self.formatter.format(record)
        message = message.split('\n')[-1]
        self.show_message(message, level=record.levelno)
