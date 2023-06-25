from __future__ import annotations

import math
from enum import Enum, IntEnum, auto, EnumMeta
from functools import partial
from typing import Any, Callable, Optional

from PySide2 import QtWidgets, QtGui, QtCore

from qt_extensions import helper
from qt_extensions.button import BaseButton
from qt_extensions.icons import MaterialIcon
from qt_extensions.resizegrip import ResizeGrip


class ParameterWidget(QtWidgets.QWidget):
    # by not using @property it is easier to set typing hints
    enabled_changed: QtCore.Signal = QtCore.Signal(bool)
    value_changed: QtCore.Signal = QtCore.Signal(object)

    _value: Any = None
    _default: Any = None
    _name: str = ''
    _label: str = ''
    _tooltip: str = ''

    def __init__(self, name: str = '', parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        if name:
            self.set_name(name)
            self.set_label(helper.title(name))

        self._init_layout()
        self._init_ui()
        self._init_defaults()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name())})'

    def _init_layout(self) -> None:
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def _init_ui(self) -> None:
        pass

    def _init_defaults(self) -> None:
        self.blockSignals(True)
        attributes = dir(self.__class__)
        for name in attributes:
            if not name.startswith('_') or name.startswith('__') or name == '_value':
                continue
            try:
                setter = getattr(self, f'set{name}')
                value = getattr(self, name)
            except AttributeError:
                continue
            setter(value)
        self.blockSignals(False)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            self.enabled_changed.emit(self.isEnabled())
        super().changeEvent(event)

    def default(self) -> Any:
        return self._default

    def label(self) -> str:
        return self._label

    def name(self) -> str:
        return self._name

    def set_default(self, default: Any) -> None:
        self.set_value(default)
        self._default = self.value()

    def set_label(self, label: str) -> None:
        self._label = label

    def set_name(self, name: str) -> None:
        self._name = name

    def set_tooltip(self, tooltip: str) -> None:
        self._tooltip = tooltip

    def set_value(self, value: Any) -> None:
        if value != self._value:
            self._value = value
            self.value_changed.emit(value)

    def tooltip(self) -> str:
        return self._tooltip

    def value(self) -> Any:
        return self._value


class IntParameter(ParameterWidget):
    value_changed: QtCore.Signal = QtCore.Signal(int)

    _value: int = 0
    _default: int = 0
    _slider_min: int = 0
    _slider_max: int = 10
    _line_min: Optional[int] = None
    _line_max: Optional[int] = None
    _slider_visible: bool = True
    _commit_on_edit: bool = False

    def _init_ui(self) -> None:
        # line
        self.line = IntLineEdit(self)
        self.line.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line)

        # slider
        self.slider = IntSlider()
        self.slider.value_changed.connect(self._slider_value_changed)
        # prevent any size changes when slider shows
        self.slider.setMaximumHeight(self.line.minimumSizeHint().height())
        self.layout().addWidget(self.slider)
        self.layout().setStretch(1, 1)

        self.setFocusProxy(self.line)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._toggle_slider(True)

    def commit_on_edit(self) -> bool:
        return self._commit_on_edit

    def line_min(self) -> int:
        return self._line_min

    def line_max(self) -> int:
        return self._line_max

    def slider_min(self) -> int:
        return self._slider_min

    def slider_max(self) -> int:
        return self._slider_max

    def slider_visible(self) -> bool:
        return self._slider_visible

    def set_commit_on_edit(self, commit_on_edit: bool) -> None:
        self._commit_on_edit = commit_on_edit
        self.line.commit_on_edit = commit_on_edit

    def set_line_min(self, line_min: Optional[int]) -> None:
        self._line_min = line_min
        self.line.set_minimum(line_min)

    def set_line_max(self, line_max: Optional[int]) -> None:
        self._line_max = line_max
        self.line.set_maximum(line_max)

    def set_slider_min(self, slider_min: int) -> None:
        self._slider_min = slider_min
        self.slider.set_minimum(slider_min)

    def set_slider_max(self, slider_max: int) -> None:
        self._slider_max = slider_max
        self.slider.set_maximum(slider_max)

    def set_slider_visible(self, slider_visible: bool) -> None:
        self._slider_visible = slider_visible
        self._toggle_slider(slider_visible)

    def set_value(self, value: int) -> None:
        super().set_value(value)
        self._set_line_value(value)
        self._set_slider_value(value)

    def value(self) -> int:
        return super().value()

    def _line_value_changed(self, value: int) -> None:
        super().set_value(value)
        self._set_slider_value(value)

    def _slider_value_changed(self, value: int) -> None:
        super().set_value(value)
        self._set_line_value(value)

    def _set_line_value(self, value: int) -> None:
        self.line.blockSignals(True)
        self.line.set_value(value)
        self.line.blockSignals(False)

    def _set_slider_value(self, value: int) -> None:
        self.slider.blockSignals(True)
        self.slider.set_value(value)
        self.slider.blockSignals(False)

    def _toggle_slider(self, value: bool) -> None:
        has_space = self.size().width() > 200
        self.slider.setVisible(self._slider_visible and value and has_space)


class FloatParameter(IntParameter):
    value_changed: QtCore.Signal = QtCore.Signal(float)

    _value: float = 0
    _default: float = 0
    _slider_min: float = 0
    _slider_max: float = 10
    _line_min: Optional[float] = None
    _line_max: Optional[float] = None
    _decimals: int = 4

    def _init_ui(self) -> None:
        # line
        self.line = FloatLineEdit(self)
        self.line.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line)

        # slider
        self.slider = FloatSlider()
        self.slider.value_changed.connect(self._slider_value_changed)
        # prevent any size changes when slider shows
        self.slider.setMaximumHeight(self.line.minimumSizeHint().height())
        self.layout().addWidget(self.slider)
        self.layout().setStretch(1, 1)

        self.setFocusProxy(self.line)

    def decimals(self) -> int:
        return self._decimals

    def set_decimals(self, decimals: int) -> None:
        self._decimals = decimals
        self.line.set_decimals(decimals)

    def set_value(self, value: float) -> None:
        super().set_value(value)

    def value(self) -> float:
        return super().value()


class StringParameter(ParameterWidget):
    value_changed: QtCore.Signal = QtCore.Signal(str)

    _value: str = ''
    _default: str = ''
    _area: bool = False
    _menu: dict | list | tuple | None = None

    def _init_ui(self) -> None:
        if self._area:
            self.text = TextEdit()
            self.text.editing_finished.connect(self._editing_finished)
            ResizeGrip(self.text)
        else:
            self.text = QtWidgets.QLineEdit()
            self.text.editingFinished.connect(self._editing_finished)
        self.layout().addWidget(self.text)
        self.setFocusProxy(self.text)

        self.menu_button = QtWidgets.QToolButton()
        self.menu_button.setAutoRaise(True)
        self.layout().addWidget(self.menu_button)
        self.menu_button.hide()

    def area(self) -> bool:
        return self._area

    def menu(self) -> dict | list | tuple | None:
        return self._menu

    def set_area(self, area: bool) -> None:
        self._area = area
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        self._init_ui()

    def set_menu(self, menu: dict | list | tuple | None) -> None:
        self._menu = menu

        # update menu
        if not self._area and self._menu is not None:
            if not self.menu_button.defaultAction():
                # build dynamically for optimization
                icon = MaterialIcon('expand_more')
                action = QtWidgets.QAction(icon, 'Fill', self)
                action.triggered.connect(self._show_menu)
                self.menu_button.setDefaultAction(action)
            self.menu_button.show()
        else:
            self.menu_button.hide()

    def set_value(self, value: str) -> None:
        super().set_value(value)
        self.text.blockSignals(True)
        if self._area:
            self.text.setPlainText(value)
        else:
            self.text.setText(value)
        self.text.blockSignals(False)

    def value(self) -> str:
        return super().value()

    def _build_menu(
        self, content: dict | list | tuple, menu: QtWidgets.QMenu | None = None
    ) -> QtWidgets.QMenu:
        if menu is None:
            menu = QtWidgets.QMenu(self)
        if isinstance(content, (list, tuple)):
            content = {i: i for i in content}
        for label, text in content.items():
            if isinstance(text, dict):
                sub_menu = menu.addMenu(label)
                self._build_menu(text, sub_menu)
            else:
                action = QtWidgets.QAction(label, self)
                action.triggered.connect(partial(self.set_value, str(text)))
                menu.addAction(action)
        return menu

    def _editing_finished(self) -> None:
        if self._area:
            value = self.text.toPlainText()
        else:
            value = self.text.text()
        super().set_value(value)

    def _show_menu(self) -> None:
        relative_pos = self.menu_button.rect().topRight()
        relative_pos.setX(relative_pos.x() + 2)
        position = self.menu_button.mapToGlobal(relative_pos)

        menu = self._build_menu(self._menu)
        menu.exec_(position)
        self.menu_button.setDown(False)


class PathParameter(ParameterWidget):
    class Method(IntEnum):
        OPEN_FILE = auto()
        SAVE_FILE = auto()
        EXISTING_DIR = auto()

    OPEN_FILE = Method.OPEN_FILE
    SAVE_FILE = Method.SAVE_FILE
    EXISTING_DIR = Method.EXISTING_DIR

    value_changed: QtCore.Signal = QtCore.Signal(str)

    _value: str = ''
    _default: str = ''
    _method: Method = OPEN_FILE
    _dir_fallback: str = ''

    def _init_ui(self) -> None:
        self.line = QtWidgets.QLineEdit()
        self.line.editingFinished.connect(self._editing_finished)
        self.layout().addWidget(self.line)

        self.button = QtWidgets.QToolButton()
        self.button.setIcon(MaterialIcon('file_open'))
        self.button.clicked.connect(self.browse)
        self.layout().addWidget(self.button)

        self.layout().setStretch(0, 1)
        self.setFocusProxy(self.line)

    def browse(self) -> None:
        start_dir = self._value or self._dir_fallback
        if self._method == PathParameter.OPEN_FILE:
            path, filters = QtWidgets.QFileDialog.getOpenFileName(
                parent=self,
                caption='Open File',
                dir=start_dir,
            )
        elif self._method == PathParameter.SAVE_FILE:
            path, filters = QtWidgets.QFileDialog.getSaveFileName(
                parent=self,
                caption='Save File',
                dir=start_dir,
                filter='*.*',
            )
        elif self._method == PathParameter.EXISTING_DIR:
            path = QtWidgets.QFileDialog.getExistingDirectory(
                parent=self,
                caption='Select Directory',
                dir=start_dir,
            )
        else:
            return

        if path:
            self.set_value(path)

    def dir_fallback(self) -> str:
        return self._dir_fallback

    def method(self) -> Method:
        return self._method

    def set_dir_fallback(self, dir_fallback: str) -> None:
        self._dir_fallback = dir_fallback

    def set_method(self, method: Method) -> None:
        self._method = method

    def set_value(self, value: str) -> None:
        super().set_value(value)
        self.line.blockSignals(True)
        self.line.setText(value)
        self.line.blockSignals(False)

    def value(self) -> str:
        return super().value()

    def _editing_finished(self) -> None:
        value = self.line.text()
        super().set_value(value)


class EnumParameter(ParameterWidget):
    _value: Enum = None
    _default: Enum = None
    _formatter: Callable = staticmethod(helper.title)
    _enum: EnumMeta | None = None

    def _init_ui(self) -> None:
        self.combo = QtWidgets.QComboBox()
        self.combo.currentIndexChanged.connect(self._current_index_changed)

        self.layout().addWidget(self.combo)
        self.setFocusProxy(self.combo)

    def enum(self) -> EnumMeta:
        return self._enum

    def formatter(self) -> Callable:
        return self._formatter

    def set_enum(self, enum: EnumMeta) -> None:
        self._enum = enum
        self._update_items()
        self.combo.setCurrentIndex(0)

    def set_formatter(self, formatter: Callable) -> None:
        self._formatter = formatter
        index = self.combo.currentIndex()
        self._update_items()
        self.combo.setCurrentIndex(index)

    def set_value(self, value: Any) -> None:
        value = self._enum_from_value(value)
        super().set_value(value)

        self.combo.blockSignals(True)
        if value is None:
            index = -1
        else:
            index = self.combo.findData(value.value)
        self.combo.setCurrentIndex(index)
        self.combo.blockSignals(False)

    def value(self) -> Enum | None:
        return super().value()

    def _current_index_changed(self, index: int) -> None:
        value = self.combo.itemData(index)
        value = self._enum_from_value(value)
        super().set_value(value)

    def _enum_from_value(self, value: Any) -> Enum | None:
        try:
            # value is Enum
            if isinstance(value, self._enum):
                return value
        except TypeError:
            pass

        try:
            # value is Enum.name
            return self._enum[value]
        except KeyError:
            pass
        except TypeError:
            return None

        try:
            # value is Enum.value
            return self._enum(value)
        except (ValueError, TypeError):
            return None

    def _update_items(self) -> None:
        self.combo.blockSignals(True)
        for index in reversed(range(self.combo.count())):
            self.combo.removeItem(index)

        if isinstance(self._enum, EnumMeta):
            for member in self._enum:
                label = self._formatter(member.name)
                self.combo.addItem(label, member.value)
        self.combo.blockSignals(False)


class BoolParameter(ParameterWidget):
    value_changed: QtCore.Signal = QtCore.Signal(bool)

    _value: bool = False
    _default: bool = False

    def _init_ui(self) -> None:
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.toggled.connect(super().set_value)
        self.layout().addWidget(self.checkbox)
        self.layout().addStretch()
        self.setFocusProxy(self.checkbox)

    def set_value(self, value: bool) -> None:
        super().set_value(value)
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(value)
        self.checkbox.blockSignals(False)

    def value(self) -> bool:
        return super().value()


class ColorParameter(ParameterWidget):
    value_changed: QtCore.Signal = QtCore.Signal(QtGui.QColor)

    _value: QtGui.QColor = QtGui.QColor(0, 0, 0)
    _default: QtGui.QColor = QtGui.QColor(0, 0, 0)
    _color_min: Optional[float] = 0
    _color_max: Optional[float] = 1
    _decimals: int = 2

    def _init_ui(self) -> None:
        self.lines = []
        for i in range(3):
            line = FloatLineEdit()
            line.value_changed.connect(lambda: self._line_value_changed())
            self.lines.append(line)
            self.layout().addWidget(line)

        self.button = QtWidgets.QPushButton()
        self.button.clicked.connect(self.select_color)
        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        size = self.button.sizeHint()
        self.button.setMaximumWidth(size.height())
        self.layout().addWidget(self.button)

    def color_min(self) -> float:
        return self._color_min

    def color_max(self) -> float:
        return self._color_max

    def decimals(self) -> int:
        return self._decimals

    def select_color(self) -> None:
        color = QtWidgets.QColorDialog.getColor(
            initial=self._value, options=QtWidgets.QColorDialog.DontUseNativeDialog
        )
        if color.isValid():
            super().set_value(color)
            self._set_line_value(color)
            self._set_button_value(color)

    def set_color_min(self, color_min: float) -> None:
        self._color_min = color_min
        for line in self.lines:
            line.set_minimum(self._color_min)

    def set_color_max(self, color_max: float) -> None:
        self._color_max = color_max
        for line in self.lines:
            line.set_maximum(self._color_max)

    def set_decimals(self, decimals: int) -> None:
        self._decimals = decimals
        for line in self.lines:
            line.set_decimals(self._decimals)

    def set_value(self, value: QtGui.QColor | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtGui.QColor(*value[:4])
        super().set_value(value)
        self._set_button_value(value)
        self._set_line_value(value)

    def value(self) -> QtGui.QColor:
        return super().value()

    def _line_value_changed(self) -> None:
        value = QtGui.QColor.fromRgbF(
            self.lines[0].value(), self.lines[1].value(), self.lines[2].value()
        )
        super().set_value(value)
        self._set_button_value(value)

    def _set_button_value(self, value: QtGui.QColor) -> None:
        self.button.setPalette(QtGui.QPalette(value))

    def _set_line_value(self, value: QtGui.QColor) -> None:
        rgb = value.getRgbF()
        for i, line in enumerate(self.lines):
            line.blockSignals(True)
            line.set_value(rgb[i])
            line.blockSignals(False)


class PointParameter(ParameterWidget):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QPoint)

    _value: QtCore.QPoint = QtCore.QPoint(0, 0)
    _default: QtCore.QPoint = QtCore.QPoint(0, 0)
    _line_min: Optional[int] = None
    _line_max: Optional[int] = None

    def _init_ui(self) -> None:
        self.line1 = IntLineEdit()
        self.line1.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line1)

        self.line2 = IntLineEdit()
        self.line2.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line2)

        self.setFocusProxy(self.line1)

    def default(self) -> QtCore.QPoint:
        return super().default()

    def line_max(self) -> Optional[int]:
        return self._line_max

    def line_min(self) -> Optional[int]:
        return self._line_min

    def set_line_max(self, line_max: Optional[int]) -> None:
        self._line_max = line_max
        self.line1.set_maximum(line_max)
        self.line2.set_maximum(line_max)

    def set_line_min(self, line_min: Optional[int]) -> None:
        self._line_min = line_min
        self.line1.set_minimum(line_min)
        self.line2.set_minimum(line_min)

    def set_value(self, value: QtCore.QPoint | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QPoint(value[0], value[1])
        super().set_value(value)
        self.line1.blockSignals(True)
        self.line1.set_value(value.x())
        self.line1.blockSignals(False)
        self.line2.blockSignals(True)
        self.line2.set_value(value.y())
        self.line2.blockSignals(False)

    def value(self) -> QtCore.QPoint:
        return super().value()

    def _line_value_changed(self, value: int) -> None:
        value = QtCore.QPoint(self.line1.value(), self.line2.value())
        super().set_value(value)


class PointFParameter(PointParameter):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QPointF)

    _value: QtCore.QPointF = QtCore.QPointF(0, 0)
    _default: QtCore.QPointF = QtCore.QPointF(0, 0)
    _line_min: Optional[float] = None
    _line_max: Optional[float] = None
    _decimals: int = 4

    def _init_ui(self) -> None:
        self.line1 = FloatLineEdit()
        self.line1.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line1)

        self.line2 = FloatLineEdit()
        self.line2.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line2)

        self.setFocusProxy(self.line1)

    def decimals(self) -> int:
        return self._decimals

    def set_decimals(self, decimals: int) -> None:
        self._decimals = decimals
        self.line1.set_decimals(decimals)
        self.line2.set_decimals(decimals)

    def set_value(self, value: QtCore.QPointF | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QPointF(value[0], value[1])
        super().set_value(value)

    def value(self) -> QtCore.QPointF:
        return super().value()

    def _line_value_changed(self, value: float) -> None:
        value = QtCore.QPointF(self.line1.value(), self.line2.value())
        super().set_value(value)


class SizeParameter(IntParameter):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QSize)

    _value: QtCore.QSize = QtCore.QSize(0, 0)
    _default: QtCore.QSize = QtCore.QSize(0, 0)
    _line_min: Optional[int] = None
    _line_max: Optional[int] = None
    _slider_min: int = 0
    _slider_max: int = 10
    _keep_ratio: bool = True
    _ratio_visible: bool = True

    def _init_ui(self) -> None:
        # lines
        self.line1 = IntLineEdit()
        self.line1.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line1)

        self.line2 = IntLineEdit()
        self.line2.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line2)

        # slider
        self.slider = IntSlider()
        self.slider.valueChanged.connect(self._slider_value_changed)
        # prevent any size changes when slider shows
        line_height = self.line1.minimumSizeHint().height()
        self.slider.setMaximumHeight(line_height)
        self.layout().addWidget(self.slider)
        self.layout().setStretch(2, 1)

        # keep ratio button
        self.keep_ratio_button = RatioButton()
        self.keep_ratio_button.setMaximumSize(line_height, line_height)
        self.keep_ratio_button.toggled.connect(self.set_keep_ratio)
        self.layout().addWidget(self.keep_ratio_button)

        self.setFocusProxy(self.line1)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        QtWidgets.QWidget.resizeEvent(self, event)
        if self._keep_ratio:
            self._toggle_slider(True)

    def set_commit_on_edit(self, commit_on_edit: bool) -> None:
        self._commit_on_edit = commit_on_edit
        self.line1.commit_on_edit = commit_on_edit
        self.line2.commit_on_edit = commit_on_edit

    def set_keep_ratio(self, keep_ratio: bool) -> None:
        self._keep_ratio = keep_ratio
        self.keep_ratio_button.setChecked(keep_ratio)
        self.line2.setVisible(not keep_ratio)
        self._toggle_slider(keep_ratio)
        if self.line1.value() != self.line2.value():
            self.line2.set_value(self.line1.value())

    def set_line_min(self, line_min: int) -> None:
        self._line_min = line_min
        self.line1.set_minimum(line_min)
        self.line2.set_minimum(line_min)

    def set_line_max(self, line_max: int) -> None:
        self._line_max = line_max
        self.line1.set_maximum(line_max)
        self.line2.set_maximum(line_max)

    def set_ratio_visible(self, ratio_visible: bool) -> None:
        self._ratio_visible = ratio_visible
        self.keep_ratio_button.setVisible(ratio_visible)
        self.line2.setVisible(not ratio_visible)
        if not ratio_visible:
            self.set_keep_ratio(False)

    def set_value(self, value: QtCore.QSize | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QSize(value[0], value[1])
        if value.width() != value.height():
            self.set_keep_ratio(False)
        if self._keep_ratio:
            value.setHeight(value.width())
        ParameterWidget.set_value(self, value)
        self._set_slider_value(value.width())
        self._set_line_value(value)

    def value(self) -> QtCore.QSize:
        return ParameterWidget.value(self)

    def _line_value_changed(self, value: int) -> None:
        if self._keep_ratio:
            value = QtCore.QSize(self.line1.value(), self.line1.value())
            self.line2.set_value(self.line1.value())
        else:
            value = QtCore.QSize(self.line1.value(), self.line2.value())
        ParameterWidget.set_value(self, value)
        self._set_slider_value(value.width())

    def _slider_value_changed(self, value: int) -> None:
        value = QtCore.QSize(value, value)
        ParameterWidget.set_value(self, value)
        self._set_line_value(value)

    def _set_line_value(self, value: QtCore.QSize) -> None:
        self.line1.blockSignals(True)
        self.line1.set_value(value.width())
        self.line1.blockSignals(False)
        self.line2.blockSignals(True)
        self.line2.set_value(value.height())
        self.line2.blockSignals(False)


class SizeFParameter(SizeParameter):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QSizeF)

    _value: QtCore.QSizeF = QtCore.QSizeF(0, 0)
    _default: QtCore.QSizeF = QtCore.QSizeF(0, 0)
    _line_min: Optional[float] = None
    _line_max: Optional[float] = None
    _slider_min: float = 0
    _slider_max: float = 10
    _decimals: int = 4

    def _init_ui(self) -> None:
        # lines
        self.line1 = FloatLineEdit()
        self.line1.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line1)

        self.line2 = FloatLineEdit()
        self.line2.value_changed.connect(self._line_value_changed)
        self.layout().addWidget(self.line2)

        # slider
        self.slider = FloatSlider()
        self.slider.value_changed.connect(self._slider_value_changed)
        # prevent any size changes when slider shows
        line_height = self.line1.minimumSizeHint().height()
        self.slider.setMaximumHeight(line_height)
        self.layout().addWidget(self.slider)
        self.layout().setStretch(2, 1)

        # keep ratio button
        self.keep_ratio_button = RatioButton()
        self.keep_ratio_button.setMaximumSize(line_height, line_height)
        self.keep_ratio_button.toggled.connect(self.set_keep_ratio)
        self.layout().addWidget(self.keep_ratio_button)

        self.setFocusProxy(self.line1)

    def decimals(self) -> int:
        return self._decimals

    def set_decimals(self, decimals: int) -> None:
        self._decimals = decimals
        self.line1.set_decimals(decimals)
        self.line2.set_decimals(decimals)

    def set_value(self, value: QtCore.QSizeF | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QSizeF(value[0], value[1])
        ParameterWidget.set_value(self, value)
        self._set_slider_value(value.width())
        self._set_line_value(value)

    def value(self) -> QtCore.QSizeF:
        return super().value()

    def _line_value_changed(self, value: float) -> None:
        value = QtCore.QSizeF(self.line1.value(), self.line2.value())
        if self._keep_ratio:
            value.setHeight(value.width())
            self.line2.set_value(self.line1.value())
        ParameterWidget.set_value(self, value)
        self._set_slider_value(value.width())

    def _slider_value_changed(self, value: float) -> None:
        value = QtCore.QSizeF(value, value)
        ParameterWidget.set_value(self, value)
        self._set_line_value(value)

    def _set_slider_value(self, value: float) -> None:
        super()._set_slider_value(value)


class IntLineEdit(QtWidgets.QLineEdit):
    value_changed = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._init_validator()

        self._abs_minimum = self.validator().bottom()
        self._abs_maximum = self.validator().top()
        self._minimum = self._abs_minimum
        self._maximum = self._abs_maximum
        self._value = 0

        self.commit_on_edit = False

        self.editingFinished.connect(self.commit)
        self.textEdited.connect(self._text_edit)

    def _init_validator(self) -> None:
        validator = IntValidator()
        self.setValidator(validator)

    def commit(self, update_text: bool = True) -> None:
        # strip padding
        value = self._text_to_value(self.text())
        if int(value) == value:
            value = int(value)
        if value != self._value:
            self._value = value
            self.value_changed.emit(value)
        if update_text:
            self.setText(str(value))

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_Up:
            self._step(add=True)
            event.accept()
        elif event.key() == QtCore.Qt.Key_Down:
            self._step(add=False)
            event.accept()
        else:
            return super().keyPressEvent(event)

    def minimumSizeHint(self) -> QtCore.QSize:
        size = super().minimumSizeHint()
        size.setWidth(24)
        return size

    def sizeHint(self) -> QtCore.QSize:
        size = super().sizeHint()
        size.setWidth(60)
        return size

    def maximum(self) -> int:
        return self._maximum

    def minimum(self) -> int:
        return self._minimum

    def set_minimum(self, minimum: Optional[int]) -> None:
        if minimum is None:
            minimum = self._abs_minimum
        self._minimum = minimum
        self.validator().setBottom(minimum)

    def set_maximum(self, maximum: Optional[int]) -> None:
        if maximum is None:
            maximum = self._abs_maximum
        self._maximum = maximum
        self.validator().setTop(maximum)

    def set_value(self, value: int) -> None:
        text = self.validator().fixup(str(value))
        state, text_, pos_ = self.validator().validate(text, 0)
        if state == QtGui.QValidator.State.Acceptable:
            self.setText(text)
            self.commit()

    def value(self) -> int:
        return self._value

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta()
        if delta.y() > 0:
            self._step(add=True)
        elif delta.y() < 0:
            self._step(add=False)
        event.accept()

    def _match_value_to_text(self, value: int, text: str, exponent: int) -> str:
        # exponent is for subclasses
        padding = len([t for t in text if t.isdigit()])
        if value < 0:
            padding += 1
        text = f'{value:0{padding}}'
        return text

    def _step(self, add: int) -> bool:
        self.setFocus()
        text = self.text() or '0'
        position = self.cursorPosition()
        if self.hasSelectedText():
            position = self.selectionStart()

        # check if cursor is on special character
        if position < len(text) and not text[position].isdigit():
            return False

        step_index = self._step_index(text, position)
        exponent = self._step_exponent(step_index)

        # perform step
        amount = 1 if add else -1
        step = amount * pow(10, exponent)
        value = self._value + step

        # preserve padding
        text = self._match_value_to_text(value, text, exponent)

        # validate before setting new text
        state, text_, pos_ = self.validator().validate(text, 0)
        if state != QtGui.QValidator.State.Acceptable:
            return False
        self.setText(text)

        # don't commit change to preserve padding
        self._value = value
        self.value_changed.emit(value)

        # get new position and set selection
        position = self._step_index_to_position(step_index, text)
        self.setSelection(position, 1)
        return True

    def _step_exponent(self, step_index: int) -> int:
        # convert cursor position to exponent
        exponent = step_index - 1
        return exponent

    def _step_index(self, text: str, position: int) -> int:
        # get step index relative to decimal point
        # this preserves position when number gets larger or changes plus/minus sign
        step_index = len(text) - position
        # if cursor is at end, edit first digit
        step_index = max(1, step_index)
        return step_index

    def _step_index_to_position(self, step_index: int, text: str) -> int:
        position = len(text) - step_index
        return position

    def _text_edit(self):
        if self.commit_on_edit:
            self.commit(update_text=False)

    # noinspection PyMethodMayBeStatic
    def _text_to_value(self, text: str) -> int:
        try:
            return int(text)
        except ValueError:
            return 0


class FloatLineEdit(IntLineEdit):
    value_changed = QtCore.Signal(float)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._decimals = self.validator().decimals()

    def _init_validator(self) -> None:
        validator = DoubleValidator()
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)

    def commit(self, update_text: bool = True) -> None:
        # strip padding
        value = self._text_to_value(self.text())
        if value != self._value:
            self._value = value
            self.value_changed.emit(value)
        if update_text:
            if int(value) == value:
                value = int(value)
            self.setText(str(value))

    def decimals(self) -> int:
        return self._decimals

    def set_decimals(self, value: int) -> None:
        self._decimals = value
        self.validator().setDecimals(value)

    def set_value(self, value: float) -> None:
        super().set_value(value)

    def value(self) -> float:
        return super().value()

    def _match_value_to_text(self, value: int, text: str, exponent: int) -> str:
        decimal_index = text.find('.')

        # preserve padding
        if decimal_index == -1:
            padding_decimal = 0
        else:
            padding_decimal = len(text) - 1 - decimal_index
            text = text[:decimal_index]

        # preserve padding if we switch to something like 1.001 > 1.000
        padding_decimal = max(padding_decimal, -exponent)
        padding_int = len([t for t in text if t.isdigit()])
        # account for minus sign
        if value < 0:
            padding_int += 1

        # padding_int needs to contain both padding for int and decimals
        padding_int += padding_decimal + 1 * bool(padding_decimal)

        value = round(value, padding_decimal)
        text = f'{value:0{padding_int}.{padding_decimal}f}'

        return text

    def _step_exponent(self, step_index: int) -> int:
        # convert cursor position to exponent
        exponent = step_index
        # if cursor is on the decimal then edit the first decimal
        if step_index >= 0:
            exponent = step_index - 1

        return exponent

    def _step_index(self, text: str, position: int) -> int:
        # get step index relative to decimal point
        # this preserves position when number gets larger or changes plus/minus sign
        decimal_index = text.find('.')
        if decimal_index == -1:
            step_index = len(text) - position
        else:
            step_index = decimal_index - position
        return step_index

    def _step_index_to_position(self, step_index: int, text: str) -> int:
        decimal_index = text.find('.')
        position = len(text) - step_index
        if decimal_index > -1:
            # if position is on decimal point, move to first decimal
            if step_index == 0:
                step_index = -1
            position = decimal_index - step_index
        return position

    # noinspection PyMethodMayBeStatic
    def _text_to_value(self, text: str) -> float:
        try:
            return float(text)
        except ValueError:
            return float(0)


class IntValidator(QtGui.QIntValidator):
    def fixup(self, text: str) -> str:
        text = str(super().fixup(text))
        text = text.replace(',', '')
        try:
            text = str(max(min(int(text), self.top()), self.bottom()))
        except ValueError:
            pass
        return text


class DoubleValidator(QtGui.QDoubleValidator):
    def fixup(self, text: str) -> str:
        try:
            float(text)
        except ValueError:
            characters = '+-01234567890.'
            text = [t for t in text if t in characters]

        try:
            value = float(text)
            value = min(max(value, self.bottom()), self.top())
            value = round(value, self.decimals())
            text = '{value:.{decimals}f}'.format(value=value, decimals=self.decimals())
            return text
        except (ValueError, TypeError):
            return text


class IntSlider(QtWidgets.QSlider):
    def __init__(
        self,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)
        self.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.value_changed = self.valueChanged

    def set_minimum(self, value: int) -> None:
        self.setMinimum(value)
        self._update_steps()

    def set_maximum(self, value: int) -> None:
        self.setMaximum(value)
        self._update_steps()

    def set_value(self, value: int) -> None:
        self.setSliderPosition(value)

    def _exponent(self) -> int:
        # automatically adjust step size and tick interval based on slider range
        num_range = abs(self.maximum() - self.minimum())
        if num_range == 0:
            num_range = 1
        exponent = math.log10(num_range)

        # round exponent up or down with weighting towards down
        if exponent % 1 > 0.8:
            exponent = math.ceil(exponent)
        else:
            exponent = math.floor(exponent)
        return exponent

    def _update_steps(self) -> None:
        step = pow(10, max(self._exponent() - 2, 0))

        self.setSingleStep(step)
        self.setPageStep(step * 10)
        self.setTickInterval(step * 10)


class FloatSlider(IntSlider):
    _fvalue_changed: QtCore.Signal = QtCore.Signal(float)

    def __init__(
        self,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)
        super().valueChanged.connect(self._value_changed)
        self.value_changed = self._fvalue_changed

        self._minimum = super().minimum()
        self._maximum = super().maximum()

        self.setSingleStep(1)
        self.setPageStep(10)
        self.setTickInterval(10)

    def minimum(self) -> float:
        return self._minimum

    def maximum(self) -> float:
        return self._maximum

    def set_minimum(self, minimum: float) -> None:
        value = self.value()
        self._minimum = minimum
        self._update_steps()
        self.set_value(value)

    def set_maximum(self, maximum: float) -> None:
        value = self.value()
        self._maximum = maximum
        self._update_steps()
        self.set_value(value)

    def set_value(self, value: float) -> None:
        if math.isnan(value):
            return
        int_value = self._int(value)
        self.setSliderPosition(int_value)

    def value(self) -> float:
        value = super().value()
        float_value = self._float(value)
        return float_value

    def _int(self, value: float) -> int:
        # convert from float to int in slider scale
        try:
            percentage = (value - self._minimum) / (self._maximum - self._minimum)
        except ZeroDivisionError:
            return 0
        slider_range = super().maximum() - super().minimum()
        clamped_value = min(max(percentage, 0), 1) * slider_range + super().minimum()
        return int(clamped_value)

    def _float(self, value: int) -> float:
        # convert from int slider scale to float
        slider_range = super().maximum() - super().minimum()
        try:
            percentage = (value - super().minimum()) / slider_range
        except ZeroDivisionError:
            return float('nan')
        float_value = self._minimum + (self._maximum - self._minimum) * percentage
        return float_value

    def _update_steps(self) -> None:
        # find a value that brings the float range into an int range
        # with step size locked to 1 and 10
        step = pow(10, -(self._exponent() - 2))

        self.blockSignals(True)
        self.setMinimum(int(self._minimum * step))
        self.setMaximum(int(self._maximum * step))
        self.blockSignals(False)

    def _value_changed(self, value: int) -> None:
        value = self._float(value)
        if not math.isnan(value):
            self.value_changed.emit(value)


class RatioButton(BaseButton):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setIcon(MaterialIcon('link_off', size=self._icon_size))
        self.setIcon(MaterialIcon('link', size=self._icon_size), True)
        self.setMaximumSize(QtCore.QSize(self._icon_size, self._icon_size))
        self.setCheckable(True)


class TextEdit(QtWidgets.QPlainTextEdit):
    editing_finished: QtCore.Signal = QtCore.Signal()

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        self.editing_finished.emit()
        return super().focusOutEvent(event)

    def sizeHint(self) -> QtCore.QSize:
        size_hint = super().sizeHint()
        size_hint.setHeight(self.minimumSizeHint().height())
        return size_hint


__all__ = [
    'ParameterWidget',
    'IntParameter',
    'FloatParameter',
    'PointParameter',
    'PointFParameter',
    'SizeParameter',
    'SizeFParameter',
    'StringParameter',
    'PathParameter',
    'BoolParameter',
    'EnumParameter',
    'ColorParameter',
]
