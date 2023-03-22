import logging
from enum import Enum, IntEnum, auto
import math
import typing
from functools import partial
from PySide2 import QtWidgets, QtGui, QtCore
from qt_extensions import helper
from qt_extensions.icons import MaterialIcon
from qt_extensions.resizegrip import ResizeGrip


class PropertyWidget(QtWidgets.QWidget):
    # by not using @property it is easier to set typing hints
    enabled_changed: QtCore.Signal = QtCore.Signal(bool)
    value_changed: QtCore.Signal = QtCore.Signal(object)

    value: typing.Any = None
    default: typing.Any = None
    name: str | None = None
    label: str | None = None

    def __init__(
        self, name: str | None = None, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._setter_signals = {}
        self._value = None

        self.name = name
        if self.name:
            self.label = helper.title(self.name)

        self._init_layout()
        self._init_ui()
        self._init_signals()
        self._init_attrs()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)})'

    def __setattr__(self, key: str, value: typing.Any) -> None:
        super().__setattr__(key, value)
        if not hasattr(self, '_setter_signals'):
            return
        for attr in self._setter_signals.keys():
            if key == attr:
                self._setter_signals[attr](value)

    def _init_layout(self) -> None:
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def _init_ui(self) -> None:
        pass

    def _init_signals(self) -> None:
        self.setter_signal('value', self.set_value)
        self.setter_signal('_value', self._set_value)
        self.setter_signal('default', self.set_default)

    def _init_attrs(self) -> None:
        # trigger all signals once to initialize the widget
        self.blockSignals(True)
        for attr in self._setter_signals.keys():
            value = getattr(self, attr)
            self._setter_signals[attr](value)
        self.value = self.default
        self.blockSignals(False)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            self.enabled_changed.emit(self.isEnabled())
        super().changeEvent(event)

    def init_from(self, instance) -> None:
        if not isinstance(instance, self.__class__):
            raise TypeError('instance needs to be the same type as self')

        class_attrs = instance._class_attrs()

        # set default values
        current_value = class_attrs.pop('value', None)
        for attr, value in class_attrs.items():
            setattr(self, attr, value)
        self.value = current_value

    def set_value(self, value: typing.Any) -> None:
        self.value_changed.emit(value)

    def set_default(self, value: typing.Any) -> None:
        self.value = value

    def setter_signal(self, attr: str, func: typing.Callable) -> None:
        # helper function to register signals when attrs are set
        self._setter_signals[attr] = func

    def _class_attrs(self) -> dict[str, typing.Any]:
        # get default values based on annotations
        class_attrs = {}
        cls = self.__class__
        while issubclass(cls, PropertyWidget):
            for key, type_ in cls.__annotations__.items():
                value = getattr(self, key)
                if key not in class_attrs and not isinstance(value, QtCore.Signal):
                    class_attrs[key] = value
            cls = cls.__base__
        return class_attrs

    def _set_value(self, value: typing.Any) -> None:
        # this is only used internally to not trigger any recursive loops
        super().__setattr__('value', value)
        self.value_changed.emit(value)


class IntProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(int)

    value: int = 0
    default: int = 0
    slider_min: int = 0
    slider_max: int = 10
    line_min: int | None = None
    line_max: int | None = None
    slider_visible: bool = True

    def _init_ui(self) -> None:
        # line
        self.line = IntLineEdit(self)
        self.line.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line)

        # slider
        self.slider = IntSlider()
        self.slider.valueChanged.connect(self._slider_value_change)
        self.slider.setVisible(False)
        # prevent any size changes when slider shows
        self.slider.setMaximumHeight(self.line.minimumSizeHint().height())
        self.layout().addWidget(self.slider)
        self.layout().setStretch(1, 1)

        self.setFocusProxy(self.line)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('line_min', partial(setattr, self.line, 'minimum'))
        self.setter_signal('line_max', partial(setattr, self.line, 'maximum'))
        self.setter_signal('slider_min', self.slider.setMinimum)
        self.setter_signal('slider_max', self.slider.setMaximum)
        self.setter_signal('slider_visible', self.toggle_slider)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.toggle_slider(True)

    def set_value(self, value: int) -> None:
        super().set_value(value)
        self.set_line_value(value)
        self.set_slider_value(value)

    def set_line_value(self, value: int) -> None:
        self.line.blockSignals(True)
        self.line.value = value
        self.line.blockSignals(False)

    def set_slider_value(self, value: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setSliderPosition(value)
        self.slider.blockSignals(False)

    def toggle_slider(self, value: bool) -> None:
        has_space = self.size().width() > 200
        self.slider.setVisible(self.slider_visible and value and has_space)

    def _line_value_change(self, value: int) -> None:
        self._value = value
        self.set_slider_value(value)

    def _slider_value_change(self, value: int) -> None:
        self._value = value
        self.set_line_value(value)


class FloatProperty(IntProperty):
    value_changed: QtCore.Signal = QtCore.Signal(float)

    value: float = 0
    default: float = 0
    slider_min: float = 0
    slider_max: float = 10
    line_min: float | None = None
    line_max: float | None = None
    decimals: int = 4

    def _init_ui(self) -> None:
        # line
        self.line = FloatLineEdit(self)
        self.line.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line)

        # slider
        self.slider = FloatSlider()
        self.slider.valueChanged.connect(self._slider_value_change)
        self.slider.setVisible(False)
        # prevent any size changes when slider shows
        self.slider.setMaximumHeight(self.line.minimumSizeHint().height())
        self.layout().addWidget(self.slider)
        self.layout().setStretch(1, 1)

        self.setFocusProxy(self.line)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('decimals', partial(setattr, self.line, 'decimals'))


class StringProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(str)

    value: str = ''
    default: str = ''
    area: bool = False
    menu: dict | None = None

    def _init_ui(self) -> None:
        if self.area:
            self.text = TextEdit()
            self.text.editing_finished.connect(self._editing_finish)
            ResizeGrip(self.text)
        else:
            self.text = QtWidgets.QLineEdit()
            self.text.editingFinished.connect(self._editing_finish)
        self.layout().addWidget(self.text)
        self.setFocusProxy(self.text)

        self.menu_button = QtWidgets.QToolButton()
        self.menu_button.setAutoRaise(True)
        self.layout().addWidget(self.menu_button)
        self.menu_button.hide()

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('area', lambda _: self.update_layout())
        self.setter_signal('menu', self._update_menu)

    def set_value(self, value: str) -> None:
        super().set_value(value)
        self.text.blockSignals(True)
        if self.area:
            self.text.setPlainText(value)
        else:
            self.text.setText(value)
        self.text.blockSignals(False)

    def update_layout(self) -> None:
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        self._init_ui()

    def _editing_finish(self) -> None:
        if self.area:
            value = self.text.toPlainText()
        else:
            value = self.text.text()
        self._value = value

    def _update_menu(self, menu: dict | None) -> None:
        if not self.area and self.menu is not None:
            if not self.menu_button.defaultAction():
                icon = MaterialIcon('expand_more')
                action = QtWidgets.QAction(icon, 'Fill', self)
                action.triggered.connect(self._request_menu)
                self.menu_button.setDefaultAction(action)
            self.menu_button.show()
        else:
            self.menu_button.hide()

    def _request_menu(self) -> None:
        relative_pos = self.menu_button.rect().topRight()
        relative_pos.setX(relative_pos.x() + 2)
        position = self.menu_button.mapToGlobal(relative_pos)

        menu = self._menu(self.menu)
        menu.exec_(position)
        self.menu_button.setDown(False)

    def _menu(
        self, content: dict, menu: QtWidgets.QMenu | None = None
    ) -> QtWidgets.QMenu:
        if menu is None:
            menu = QtWidgets.QMenu(self)
        for label, text in content.items():
            if isinstance(text, dict):
                sub_menu = menu.addMenu(label)
                self._menu(text, sub_menu)
            else:
                action = QtWidgets.QAction(label, self)
                action.triggered.connect(partial(self.set_value, str(text)))
                menu.addAction(action)
        return menu


class PathProperty(PropertyWidget):
    class Method(IntEnum):
        OPEN_FILE = auto()
        SAVE_FILE = auto()
        EXISTING_DIR = auto()

    value_changed: QtCore.Signal = QtCore.Signal(str)

    value: str = ''
    default: str = ''
    method: Method = Method.OPEN_FILE

    def _init_ui(self) -> None:
        self.line = QtWidgets.QLineEdit()
        self.line.editingFinished.connect(self._editing_finish)
        self.layout().addWidget(self.line)

        self.button = QtWidgets.QToolButton()
        self.button.clicked.connect(self.browse)
        self.button.setText('...')
        self.layout().addWidget(self.button)

        self.layout().setStretch(0, 1)
        self.setFocusProxy(self.line)

    def browse(self) -> None:
        match self.method:
            case PathProperty.Method.OPEN_FILE:
                path, filters = QtWidgets.QFileDialog.getOpenFileName(
                    parent=self,
                    caption='Open File',
                    dir=self.value,
                )
            case PathProperty.Method.SAVE_FILE:
                path, filters = QtWidgets.QFileDialog.getSaveFileName(
                    parent=self,
                    caption='Save File',
                    dir=self.value,
                    filter='*.*',
                )
            case PathProperty.Method.EXISTING_DIR:
                path = QtWidgets.QFileDialog.getExistingDirectory(
                    parent=self,
                    caption='Select Directory',
                    dir=self.value,
                )
            case _:
                return

        if path:
            self.value = path

    def set_value(self, value: str) -> None:
        super().set_value(value)
        self.line.blockSignals(True)
        self.line.setText(value)
        self.line.blockSignals(False)

    def _editing_finish(self) -> None:
        value = self.line.text()
        self._value = value


class EnumProperty(PropertyWidget):
    # TODO: figure out how to actually handle it
    # EnumProperty's value is actually not of type value but whatever the type of the enum.value is.
    # this is bad because enumproperty.value = Enum.RED means that enumproperty.value is now 'red'

    value_changed: QtCore.Signal = QtCore.Signal(Enum)

    value: typing.Any | None = None
    default: Enum | None = None
    formatter: typing.Callable = staticmethod(helper.title)
    enum: Enum | None = None

    def _init_ui(self) -> None:
        self.combo = QtWidgets.QComboBox()
        self.combo.currentIndexChanged.connect(self._current_index_change)

        self.layout().addWidget(self.combo)
        # self.layout().addStretch()
        self.setFocusProxy(self.combo)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('formatter', lambda _: self.update_items())
        self.setter_signal('enum', lambda _: self.update_items())

    def set_value(self, value: Enum | None) -> None:
        super().set_value(value)

        if value is not None and isinstance(value, self.enum):
            index = self.combo.findData(value.value)
            self.combo.setCurrentIndex(index)

    def update_items(self) -> None:
        for index in reversed(range(self.combo.count())):
            self.combo.removeItem(index)

        if self.enum is not None:
            for member in self.enum:
                label = self.formatter(member.name)
                self.combo.addItem(label, member.value)
            self._value = self.combo.itemData(0)

    def _current_index_change(self, index: int) -> None:
        self._value = self.combo.itemData(index)

    def _set_value(self, value: typing.Any) -> None:
        if isinstance(value, Enum):
            value = value.value
        super()._set_value(value)


class BoolProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(bool)

    value: bool = False
    default: bool = False

    def _init_ui(self) -> None:
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.toggled.connect(self._value_change)
        self.layout().addWidget(self.checkbox)
        self.layout().addStretch()
        self.setFocusProxy(self.checkbox)

    def _value_change(self, value: bool) -> None:
        self._value = value

    def set_value(self, value: bool) -> None:
        super().set_value(value)
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(value)
        self.checkbox.blockSignals(False)


class PointProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QPoint)

    value: QtCore.QPoint = QtCore.QPoint(0, 0)
    default: QtCore.QPoint = QtCore.QPoint(0, 0)
    line_min: int | None = None
    line_max: int | None = None

    def _init_ui(self) -> None:
        self.line1 = IntLineEdit()
        self.line1.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line1)

        self.line2 = IntLineEdit()
        self.line2.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line2)

        self.setFocusProxy(self.line1)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('line_min', lambda _: self.update_lines())
        self.setter_signal('line_max', lambda _: self.update_lines())

    def _line_value_change(self, _) -> None:
        value = QtCore.QPoint(self.line1.value, self.line2.value)
        self._value = value

    def set_value(self, value: QtCore.QPoint | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QPoint(value[0], value[1])
        super().set_value(value)
        self.line1.blockSignals(True)
        self.line1.value = value.x()
        self.line1.blockSignals(False)
        self.line2.blockSignals(True)
        self.line2.value = value.y()
        self.line2.blockSignals(False)

    def update_lines(self) -> None:
        self.line1.minimum = self.line_min
        self.line1.maximum = self.line_max
        self.line2.minimum = self.line_min
        self.line2.maximum = self.line_max


class PointFProperty(PointProperty):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QPointF)

    value: QtCore.QPointF = QtCore.QPointF(0, 0)
    default: QtCore.QPointF = QtCore.QPointF(0, 0)
    line_min: float | None = None
    line_max: float | None = None
    decimals: int = 4

    def _init_ui(self) -> None:
        self.line1 = FloatLineEdit()
        self.line1.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line1)

        self.line2 = FloatLineEdit()
        self.line2.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line2)

        self.setFocusProxy(self.line1)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('decimals', self.update_decimals)

    def _line_value_change(self, _) -> None:
        value = QtCore.QPointF(self.line1.value, self.line2.value)
        self._value = value

    def set_value(self, value: QtCore.QPointF | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QPointF(value[0], value[1])
        super().set_value(value)

    def update_decimals(self, decimals):
        self.line1.decimals = decimals
        self.line2.decimals = decimals


class SizeProperty(IntProperty):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QSize)

    value: QtCore.QSize = QtCore.QSize(0, 0)
    default: QtCore.QSize = QtCore.QSize(0, 0)
    line_min: int | None = None
    line_max: int | None = None
    slider_min: int = 0
    slider_max: int = 10
    keep_ratio: bool = True
    ratio_visible: bool = True

    def _init_ui(self) -> None:
        # lines
        self.line1 = IntLineEdit()
        self.line1.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line1)

        self.line2 = IntLineEdit()
        self.line2.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line2)

        # slider
        self.slider = IntSlider()
        self.slider.valueChanged.connect(self._slider_value_change)
        self.slider.setVisible(False)
        # prevent any size changes when slider shows
        line_height = self.line1.minimumSizeHint().height()
        self.slider.setMaximumHeight(line_height)
        self.layout().addWidget(self.slider)
        self.layout().setStretch(2, 1)

        # keep ratio button
        self.keep_ratio_button = LinkButton()
        self.keep_ratio_button.setMaximumSize(line_height, line_height)
        self.keep_ratio_button.toggled.connect(partial(setattr, self, 'keep_ratio'))
        self.layout().addWidget(self.keep_ratio_button)

        self.setFocusProxy(self.line1)

    def _init_signals(self) -> None:
        PropertyWidget._init_signals(self)
        self.setter_signal('line_min', lambda _: self.update_lines())
        self.setter_signal('line_max', lambda _: self.update_lines())
        self.setter_signal('slider_min', self.slider.setMinimum)
        self.setter_signal('slider_max', self.slider.setMaximum)
        self.setter_signal('slider_visible', self.toggle_slider)
        self.setter_signal('keep_ratio', self._keep_ratio_toggle)
        self.setter_signal('ratio_visible', self.toggle_ratio)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        QtWidgets.QWidget.resizeEvent(self, event)
        if self.keep_ratio:
            self.toggle_slider(True)

    def set_line_value(self, value: QtCore.QSize) -> None:
        self.line1.blockSignals(True)
        self.line1.value = value.width()
        self.line1.blockSignals(False)
        self.line2.blockSignals(True)
        self.line2.value = value.height()
        self.line2.blockSignals(False)

    def set_slider_value(self, value: QtCore.QSize) -> None:
        self.slider.blockSignals(True)
        self.slider.setSliderPosition(value.width())
        self.slider.blockSignals(False)

    def set_value(self, value: QtCore.QSize | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QSize(value[0], value[1])
        if self.keep_ratio:
            value.setHeight(value.width())
        super().set_value(value)

    def toggle_ratio(self, value: bool) -> None:
        self.keep_ratio_button.setVisible(value)
        if not value:
            self.keep_ratio = False

    def update_lines(self) -> None:
        self.line1.minimum = self.line_min
        self.line1.maximum = self.line_max
        self.line2.minimum = self.line_min
        self.line2.maximum = self.line_max

    def _keep_ratio_toggle(self, value: QtCore.QSize) -> None:
        self.keep_ratio_button.setChecked(value)
        self.line2.setVisible(not value)
        self.toggle_slider(value)

    def _line_value_change(self, _) -> None:
        value = QtCore.QSize(self.line1.value, self.line2.value)
        self._value = value
        self.set_slider_value(value)

    def _slider_value_change(self, value) -> None:
        value = QtCore.QSize(value, value)
        self._value = value
        self.set_line_value(value)


class SizeFProperty(SizeProperty):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QSizeF)

    value: QtCore.QSizeF = QtCore.QSizeF(0, 0)
    default: QtCore.QSizeF = QtCore.QSizeF(0, 0)
    line_min: float | None = None
    line_max: float | None = None
    slider_min: float = 0
    slider_max: float = 10
    decimals: int = 4

    def _init_ui(self) -> None:
        # lines
        self.line1 = FloatLineEdit()
        self.line1.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line1)

        self.line2 = FloatLineEdit()
        self.line2.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line2)

        # slider
        self.slider = FloatSlider()
        self.slider.valueChanged.connect(self._slider_value_change)
        self.slider.setVisible(False)
        # prevent any size changes when slider shows
        line_height = self.line1.minimumSizeHint().height()
        self.slider.setMaximumHeight(line_height)
        self.layout().addWidget(self.slider)
        self.layout().setStretch(2, 1)

        # keep ratio button
        self.keep_ratio_button = LinkButton()
        self.keep_ratio_button.setMaximumSize(line_height, line_height)
        self.keep_ratio_button.toggled.connect(partial(setattr, self, 'keep_ratio'))
        self.layout().addWidget(self.keep_ratio_button)

        self.setFocusProxy(self.line1)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('decimals', lambda _: self.update_lines())

    def set_value(self, value: QtCore.QSizeF | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtCore.QSizeF(value[0], value[1])
        super().set_value(value)

    def update_lines(self) -> None:
        super().update_lines()
        self.line1.decimals = self.decimals
        self.line2.decimals = self.decimals

    def _line_value_change(self, _) -> None:
        value = QtCore.QSizeF(self.line1.value, self.line2.value)
        self._value = value
        self.set_slider_value(value)

    def _slider_value_change(self, value: QtCore.QSizeF) -> None:
        value = QtCore.QSizeF(value, value)
        self._value = value
        self.set_line_value(value)


class ColorProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(QtGui.QColor)

    value: QtGui.QColor = QtGui.QColor(0, 0, 0)
    default: QtGui.QColor = QtGui.QColor(0, 0, 0)
    color_min: float | None = None
    color_max: float | None = None
    decimals: int = 2

    def _init_ui(self) -> None:
        self.lines = []
        for i in range(3):
            line = FloatLineEdit()
            line.value_changed.connect(self._line_value_change)
            self.lines.append(line)
            self.layout().addWidget(line)

        self.button = QtWidgets.QPushButton()
        self.button.clicked.connect(self.select_color)
        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        size = self.button.sizeHint()
        self.button.setMaximumWidth(size.height())
        self.layout().addWidget(self.button)

    def _init_signals(self) -> None:
        super()._init_signals()
        self.setter_signal('color_min', lambda _: self.update_lines())
        self.setter_signal('color_max', lambda _: self.update_lines())
        self.setter_signal('decimals', lambda _: self.update_lines())

    def select_color(self) -> None:
        color = QtWidgets.QColorDialog.getColor(
            initial=self.value, options=QtWidgets.QColorDialog.DontUseNativeDialog
        )
        if color.isValid():
            self._value = color
            self.set_line_value(color)
            self.set_button_value(color)

    def set_button_value(self, value: QtGui.QColor) -> None:
        self.button.setPalette(QtGui.QPalette(value))

    def set_line_value(self, value: QtGui.QColor) -> None:
        rgb = value.getRgbF()
        for i, line in enumerate(self.lines):
            line.blockSignals(True)
            line.value = rgb[i]
            line.blockSignals(False)

    def set_value(self, value: QtGui.QColor | list | tuple) -> None:
        if isinstance(value, (list, tuple)):
            value = QtGui.QColor(*value[:4])
        super().set_value(value)
        self.set_button_value(value)
        self.set_line_value(value)

    def update_lines(self) -> None:
        for line in self.lines:
            line.minimum = self.color_min
            line.maximum = self.color_max
            line.decimals = self.decimals

    def _line_value_change(self, _) -> None:
        color = QtGui.QColor.fromRgbF(
            self.lines[0].value, self.lines[1].value, self.lines[2].value
        )
        self._value = color
        self.set_button_value(color)


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

        self.editingFinished.connect(self._strip_padding)

    def _init_validator(self) -> None:
        validator = IntValidator()
        self.setValidator(validator)

    @property
    def maximum(self) -> int:
        return self._maximum

    @maximum.setter
    def maximum(self, maximum: int | None) -> None:
        if maximum is None:
            maximum = self._abs_maximum
        self._maximum = maximum
        self.validator().setTop(maximum)

    @property
    def minimum(self) -> int:
        return self._minimum

    @minimum.setter
    def minimum(self, minimum: int | None) -> None:
        if minimum is None:
            minimum = self._abs_minimum
        self._minimum = minimum
        self.validator().setBottom(minimum)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        text = self.validator().fixup(str(value))
        state, text_, pos_ = self.validator().validate(text, 0)
        if state == QtGui.QValidator.State.Acceptable:
            self.setText(text)
            self._strip_padding()

    def keyPressEvent(self, event: QtGui.QResizeEvent) -> None:
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

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta()
        if delta.y() > 0:
            self._step(add=True)
        elif delta.y() < 0:
            self._step(add=False)
        event.accept()

    @staticmethod
    def _text_to_value(text: str) -> int:
        try:
            return int(text)
        except ValueError:
            return 0

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
        value = self.value + step

        # preserve padding
        text = self._match_value_to_text(value, text, exponent)

        # validate before setting new text
        state, text_, pos_ = self.validator().validate(text, 0)
        if state != QtGui.QValidator.State.Acceptable:
            return False
        self.setText(text)
        self.value = value

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

    def _strip_padding(self) -> None:
        value = self._text_to_value(self.text())
        if int(value) == value:
            value = int(value)
        if self._value != value:
            self._value = value
            self.value_changed.emit(value)

        self.setText(str(value))


class FloatLineEdit(IntLineEdit):
    value_changed = QtCore.Signal(float)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._decimals = self.validator().decimals()

    def _init_validator(self) -> None:
        validator = DoubleValidator()
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)

    @property
    def decimals(self) -> int:
        return self._decimals

    @decimals.setter
    def decimals(self, value: int) -> None:
        self._decimals = value
        self.validator().setDecimals(value)

    @staticmethod
    def _text_to_value(text: str) -> float:
        try:
            return float(text)
        except ValueError:
            return float(0)

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


class IntValidator(QtGui.QIntValidator):
    def fixup(self, text: str) -> str:
        text = super().fixup(text).replace(',', '')
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
        except ValueError:
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

        self._slider_min = self.minimum()
        self._slider_max = self.maximum()

    def setMinimum(self, value: int) -> None:
        self.blockSignals(True)
        super().setMinimum(value)
        self.blockSignals(False)
        self._slider_min = value
        self._slider_max = max(self._slider_max, value)
        self._update_steps()

    def setMaximum(self, value: int) -> None:
        self.blockSignals(True)
        super().setMaximum(value)
        self.blockSignals(False)
        self._slider_min = min(self._slider_min, value)
        self._slider_max = value
        self._update_steps()

    def _exponent(self) -> int:
        # automatically adjust step size and tick interval based on slider range
        num_range = abs(self._slider_max - self._slider_min)
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
    valueChanged: QtCore.Signal = QtCore.Signal(float)

    def __init__(
        self,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)
        super().valueChanged.connect(self._value_change)

        self.setSingleStep(1)
        self.setPageStep(10)
        self.setTickInterval(10)

    def setSliderPosition(self, value: int) -> None:
        # convert from float to int in slider scale
        try:
            percentage = (value - self._slider_min) / (
                self._slider_max - self._slider_min
            )
        except ZeroDivisionError:
            return
        slider_range = self.maximum() - self.minimum()
        clamped_value = min(max(percentage, 0), 1) * slider_range + self.minimum()
        int_value = int(clamped_value)
        super().setSliderPosition(int_value)

    def value(self) -> float:
        value = super().value()
        float_value = self._float_value(value)
        return float_value

    def _float_value(self, value: int) -> float:
        # convert from int slider scale to float
        slider_range = self.maximum() - self.minimum()
        try:
            percentage = (value - self.minimum()) / slider_range
        except ZeroDivisionError:
            return float('nan')
        float_value = (
            self._slider_min + (self._slider_max - self._slider_min) * percentage
        )
        return float_value

    def _update_steps(self) -> None:
        # find a value that brings the float range into an int range
        # with step size locked to 1 and 10
        normalize = pow(10, -(self._exponent() - 2))
        self.blockSignals(True)
        QtWidgets.QSlider.setMinimum(self, self._slider_min * normalize)
        QtWidgets.QSlider.setMaximum(self, self._slider_max * normalize)
        self.blockSignals(False)

    def _value_change(self, value: int) -> None:
        value = self._float_value(value)
        if not math.isnan(value):
            self.valueChanged.emit(value)


class LinkButton(QtWidgets.QToolButton):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        icon = MaterialIcon('link')
        self.setIcon(icon)
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        icon_size = QtCore.QSize(size, size)
        self.setMaximumSize(icon_size)
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
    'PropertyWidget',
    'IntProperty',
    'FloatProperty',
    'PointProperty',
    'PointFProperty',
    'SizeProperty',
    'SizeFProperty',
    'StringProperty',
    'PathProperty',
    'BoolProperty',
    'EnumProperty',
    'ColorProperty',
]


if __name__ == '__main__':
    main()
