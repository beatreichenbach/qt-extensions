import enum
import math
import typing
from functools import partial
from PySide2 import QtWidgets, QtGui, QtCore
from qtproperties import utils
from qtmaterialicons.icons import MaterialIcon


class PropertyWidget(QtWidgets.QWidget):
    # by not using @property it is easier to set typing hints

    value_changed: QtCore.Signal = QtCore.Signal(object)

    value: typing.Any = None
    default: typing.Any = None
    name: str | None = None
    label: str | None = None

    def __init__(
        self, name: str | None = None, parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)

        self._setter_signals = {}
        self._value = None

        self.name = name
        if self.name:
            self.label = utils.title(self.name)

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
            if key == attr or isinstance(attr, tuple) and key in attr:
                self._setter_signals[attr](value)

    def _init_layout(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def _init_ui(self):
        pass

    def _init_signals(self):
        self.setter_signal('value', self.set_value)
        self.setter_signal('_value', self._set_value)

    def _init_attrs(self):
        self.blockSignals(True)

        class_attrs = self._class_attrs()

        # set default values
        class_attrs.pop('value', None)
        for attr, value in class_attrs.items():
            setattr(self, attr, value)
        self.value = self.default

        self.blockSignals(False)

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

    def _set_value(self, value):
        # this is only used internally to not trigger any recursive loops
        self.value_changed.emit(value)
        super().__setattr__('value', value)

    def set_value(self, value):
        self.value_changed.emit(value)

    def setter_signal(self, attr: str, func: typing.Callable) -> None:
        # helper function to register signals when attrs are set
        self._setter_signals[attr] = func

    def init_from(self, instance) -> None:
        if not isinstance(instance, self.__class__):
            raise TypeError('instance needs to be the same type as self')

        class_attrs = instance._class_attrs()

        # set default values
        value = class_attrs.pop('value', None)
        for attr, value in class_attrs.items():
            setattr(self, attr, value)
        self.value = value


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

    def _init_signals(self):
        super()._init_signals()
        self.setter_signal('line_min', self.line.setMinimum)
        self.setter_signal('line_max', self.line.setMaximum)
        self.setter_signal('slider_min', self.slider.setMinimum)
        self.setter_signal('slider_max', self.slider.setMaximum)
        self.setter_signal('slider_visible', self.toggle_slider)

    def _line_value_change(self, value):
        self._value = value
        self.set_slider_value(value)

    def _slider_value_change(self, value):
        self._value = value
        self.set_line_value(value)

    def set_value(self, value):
        super().set_value(value)
        self.set_line_value(value)
        self.set_slider_value(value)

    def set_line_value(self, value):
        self.line.blockSignals(True)
        self.line.setValue(value)
        self.line.blockSignals(False)

    def set_slider_value(self, value):
        self.slider.blockSignals(True)
        self.slider.setSliderPosition(value)
        self.slider.blockSignals(False)

    def toggle_slider(self, value):
        has_space = self.size().width() > 200
        self.slider.setVisible(self.slider_visible and value and has_space)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toggle_slider(True)


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

    def _init_signals(self):
        super()._init_signals()
        self.setter_signal('decimals', self.line.setDecimals)


class StringProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(str)

    value: str = ''
    default: str = ''
    area: bool = False

    def _init_ui(self) -> None:
        if self.area:
            self.text = QtWidgets.QPlainTextEdit()
            self.text.textChanged.connect(self._text_change)
            ResizeGrip(self.text)
        else:
            self.text = QtWidgets.QLineEdit()
            self.text.textChanged.connect(self._text_change)
        self.layout().addWidget(self.text)
        self.setFocusProxy(self.text)

    def _init_signals(self):
        super()._init_signals()
        self.setter_signal('area', self.update_layout)

    def _text_change(self, value=None):
        if self.area:
            self._value = self.text.toPlainText()
        else:
            self._value = value

    def update_layout(self, _):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        self._init_ui()

    def set_value(self, value):
        super().set_value(value)
        self.text.blockSignals(True)
        if self.area:
            self.text.setPlainText(value)
        else:
            self.text.setText(value)
        self.text.blockSignals(False)


class PathProperty(PropertyWidget):
    class Method(enum.IntEnum):
        OPEN_FILE = enum.auto()
        SAVE_FILE = enum.auto()
        EXISTING_DIR = enum.auto()

    value_changed: QtCore.Signal = QtCore.Signal(str)

    value: str = ''
    default: str = ''
    method: Method = Method.OPEN_FILE

    def _init_ui(self):
        self.line = QtWidgets.QLineEdit()
        self.line.textChanged.connect(self._text_change)
        self.layout().addWidget(self.line)

        self.button = QtWidgets.QToolButton()
        self.button.clicked.connect(self.browse)
        self.button.setText('...')
        self.layout().addWidget(self.button)

        self.layout().setStretch(0, 1)
        self.setFocusProxy(self.line)

    def _text_change(self, value):
        self._value = value

    def browse(self):
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

    def set_value(self, value):
        super().set_value(value)
        self.line.blockSignals(True)
        self.line.setText(value)
        self.line.blockSignals(False)


# class EnumProperty(PropertyWidget):
#     value_changed = QtCore.Signal(Enum)
#     accepted_type = Enum
#
#     def __init__(self, *args, **kwargs):
#         if args and isinstance(args[0], self.__class__):
#             super().__init__(*args, **kwargs)
#             return
#
#         if 'enum' not in kwargs:
#             raise AttributeError(
#                 f'{self.__class__.__name__} requires argument \'enum\''
#             )
#         if 'default' not in kwargs:
#             kwargs['default'] = next(iter(kwargs['enum']))
#
#         super().__init__(*args, **kwargs)
#
#     def init_ui(self):
#         super().init_ui()
#
#         self.combo = QtWidgets.QComboBox()
#
#         formatting = lambda e: utils.title(e.name)
#         for e in self.enum:
#             # TODO: should we be able to provide a format function?
#             # e.g formatting=lambda e: e.name.title()
#             self.combo.addItem(formatting(e), e)
#         self.layout().addWidget(self.combo)
#         # self.layout().addStretch()
#         self.setFocusProxy(self.combo)
#
#     def connect_ui(self):
#         self.combo.currentIndexChanged.connect(self.combo_index_changed)
#
#     def combo_index_changed(self, index):
#         self.value_changed.emit(self.value)
#
#     @property
#     def value(self):
#         return self.combo.currentData()
#
#     @value.setter
#     def value(self, value):
#         self.validate_value(value)
#         index = self.combo.findData(value)
#         self.combo.setCurrentIndex(index)


class BoolProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(bool)

    value: bool = False
    default: bool = False

    def _init_ui(self):
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.toggled.connect(self._value_change)
        self.layout().addWidget(self.checkbox)
        self.layout().addStretch()
        self.setFocusProxy(self.checkbox)

    def _value_change(self, value):
        self._value = value

    def set_value(self, value):
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

    def _init_ui(self):
        self.line1 = IntLineEdit()
        self.line1.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line1)

        self.line2 = IntLineEdit()
        self.line2.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line2)

        self.setFocusProxy(self.line1)

    def _init_signals(self):
        super()._init_signals()
        self.setter_signal('line_min', self.update_lines)
        self.setter_signal('line_max', self.update_lines)

    def _line_value_change(self, _):
        value = QtCore.QPoint(self.line1.value, self.line2.value)
        self._value = value

    def update_lines(self, _):
        self.line1.setMinimum(self.line_min)
        self.line1.setMaximum(self.line_max)
        self.line2.setMinimum(self.line_min)
        self.line2.setMaximum(self.line_max)

    def set_value(self, value):
        if isinstance(value, (list, tuple)):
            value = QtCore.QPoint(value[0], value[1])
        super().set_value(value)
        self.line1.setValue(value.x())
        self.line2.setValue(value.y())


class PointFProperty(PointProperty):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QPointF)

    value: QtCore.QPointF = QtCore.QPointF(0, 0)
    default: QtCore.QPointF = QtCore.QPointF(0, 0)
    line_min: float | None = None
    line_max: float | None = None

    def _init_ui(self):
        self.line1 = FloatLineEdit()
        self.line1.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line1)

        self.line2 = FloatLineEdit()
        self.line2.value_changed.connect(self._line_value_change)
        self.layout().addWidget(self.line2)

        self.setFocusProxy(self.line1)

    def _line_value_change(self, _):
        value = QtCore.QPointF(self.line1.value, self.line2.value)
        self._value = value

    def set_value(self, value):
        if isinstance(value, (list, tuple)):
            value = QtCore.QPointF(value[0], value[1])
        super().set_value(value)


class SizeProperty(IntProperty):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QSize)

    value: QtCore.QSize = QtCore.QSize(0, 0)
    default: QtCore.QSize = QtCore.QSize(0, 0)
    line_min: int | None = None
    line_max: int | None = None
    slider_min: int = 0
    slider_max: int = 10
    keep_ratio: bool = True

    def _init_ui(self):
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

    def _init_signals(self):
        PropertyWidget._init_signals(self)
        self.setter_signal('line_min', self.update_lines)
        self.setter_signal('line_max', self.update_lines)
        self.setter_signal('slider_min', self.slider.setMinimum)
        self.setter_signal('slider_max', self.slider.setMaximum)
        self.setter_signal('slider_visible', self.toggle_slider)
        self.setter_signal('keep_ratio', self.keep_ratio_toggle)

    def _line_value_change(self, _):
        value = QtCore.QSize(self.line1.value, self.line2.value)
        self._value = value
        self.set_slider_value(value)

    def _slider_value_change(self, value):
        value = QtCore.QSize(value, value)
        self._value = value
        self.set_line_value(value)

    def update_lines(self, _):
        self.line1.setMinimum(self.line_min)
        self.line1.setMaximum(self.line_max)
        self.line2.setMinimum(self.line_min)
        self.line2.setMaximum(self.line_max)

    def keep_ratio_toggle(self, value):
        self.keep_ratio_button.setChecked(value)
        self.line2.setVisible(not value)
        self.toggle_slider(value)

    def set_value(self, value):
        if isinstance(value, (list, tuple)):
            value = QtCore.QSize(value[0], value[1])
        if self.keep_ratio:
            value.setHeight(value.width())
        super().set_value(value)

    def set_line_value(self, value):
        self.line1.blockSignals(True)
        self.line1.setValue(value.width())
        self.line1.blockSignals(False)
        self.line2.blockSignals(True)
        self.line2.setValue(value.height())
        self.line2.blockSignals(False)

    def set_slider_value(self, value):
        self.slider.blockSignals(True)
        self.slider.setSliderPosition(value.width())
        self.slider.blockSignals(False)

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        if self.keep_ratio:
            self.toggle_slider(True)


class SizeFProperty(SizeProperty):
    value_changed: QtCore.Signal = QtCore.Signal(QtCore.QSizeF)

    value: QtCore.QSizeF = QtCore.QSizeF(0, 0)
    default: QtCore.QSizeF = QtCore.QSizeF(0, 0)
    line_min: float | None = None
    line_max: float | None = None
    slider_min: float = 0
    slider_max: float = 10
    decimals: int = 4

    def _init_ui(self):
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

    def _init_signals(self):
        super()._init_signals()
        self.setter_signal('decimals', self.update_lines)

    def _line_value_change(self, _):
        value = QtCore.QSizeF(self.line1.value, self.line2.value)
        self._value = value
        self.set_slider_value(value)

    def _slider_value_change(self, value):
        value = QtCore.QSizeF(value, value)
        self._value = value
        self.set_line_value(value)

    def update_lines(self, _):
        super().update_lines(_)
        self.line1.setDecimals(self.decimals)
        self.line2.setDecimals(self.decimals)

    def set_value(self, value):
        if isinstance(value, (list, tuple)):
            value = QtCore.QSizeF(value[0], value[1])
        super().set_value(value)


class ColorProperty(PropertyWidget):
    value_changed: QtCore.Signal = QtCore.Signal(QtGui.QColor)

    value: QtGui.QColor = QtGui.QColor(0, 0, 0)
    default: QtGui.QColor = QtGui.QColor(0, 0, 0)
    color_min: float | None = None
    color_max: float | None = None
    decimals: int = 2

    def _init_ui(self):
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

    def _init_signals(self):
        super()._init_signals()
        self.setter_signal('color_min', self.update_lines)
        self.setter_signal('color_max', self.update_lines)
        self.setter_signal('decimals', self.update_lines)

    def _line_value_change(self, _):
        color = QtGui.QColor.fromRgbF(
            self.lines[0].value, self.lines[1].value, self.lines[2].value
        )
        self._value = color
        self.set_button_value(color)

    def update_lines(self, _):
        for line in self.lines:
            line.setMinimum(self.color_min)
            line.setMaximum(self.color_max)
            line.setDecimals(self.decimals)

    def select_color(self):
        color = QtWidgets.QColorDialog.getColor(
            initial=self.value, options=QtWidgets.QColorDialog.DontUseNativeDialog
        )
        if color.isValid():
            self._value = color
            self.set_line_value(color)
            self.set_button_value(color)

    def set_line_value(self, value):
        rgb = value.getRgbF()
        for i, line in enumerate(self.lines):
            line.blockSignals(True)
            line.setValue(rgb[i])
            line.blockSignals(False)

    def set_button_value(self, value):
        self.button.setPalette(QtGui.QPalette(value))

    def set_value(self, value):
        if isinstance(value, (list, tuple)):
            value = QtGui.QColor(*value[:4])
        super().set_value(value)
        self.set_button_value(value)
        self.set_line_value(value)


class IntLineEdit(QtWidgets.QLineEdit):
    value_changed = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.editingFinished.connect(self.strip_padding)
        self.setValidator(IntValidator())

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            self.step(add=True)
            event.accept()
        elif event.key() == QtCore.Qt.Key_Down:
            self.step(add=False)
            event.accept()
        else:
            return super().keyPressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta()
        if delta.y() > 0:
            self.step(add=True)
        elif delta.y() < 0:
            self.step(add=False)
        event.accept()

    @property
    def value(self):
        try:
            return int(self.text())
        except ValueError:
            return 0

    @value.setter
    def value(self, value):
        if value != self._value:
            self.value_changed.emit(value)
        self._value = value

    def setValue(self, value):
        text = self.validator().fixup(str(value))

        state, text_, pos_ = self.validator().validate(text, 0)
        if state == QtGui.QValidator.State.Acceptable:
            self.setText(text)
            self.strip_padding()

    def sizeHint(self):
        size = super().sizeHint()
        size.setWidth(60)
        return size

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        size.setWidth(24)
        return size

    def setMinimum(self, minimum):
        minimum = minimum or -(1 << 31)
        self.validator().setBottom(minimum)

    def setMaximum(self, maximum):
        maximum = maximum or (1 << 31) - 1
        self.validator().setTop(maximum)

    def step(self, add):
        self.setFocus()
        text = self.text() or '0'
        position = self.cursorPosition()
        if self.hasSelectedText():
            position = self.selectionStart()

        # check if cursor is on special character
        if position < len(text) and not text[position].isdigit():
            return False

        step_index = self.step_index(text, position)
        exponent = self.step_exponent(step_index)

        # perform step
        amount = 1 if add else -1
        step = amount * pow(10, exponent)
        value = self.value + step

        # preserve padding
        text = self.match_value_to_text(value, text, exponent)

        # validate before setting new text
        state, text_, pos_ = self.validator().validate(text, 0)
        if state != QtGui.QValidator.State.Acceptable:
            return False
        self.setText(text)
        self.value = value

        # get new position and set selection
        position = self.step_index_to_position(step_index, text)
        self.setSelection(position, 1)
        return True

    def match_value_to_text(self, value, text, exponent):
        # exponent is for subclasses
        padding = len([t for t in text if t.isdigit()])
        if value < 0:
            padding += 1
        text = f'{value:0{padding}}'
        return text

    def step_index(self, text, position):
        # get step index relative to decimal point
        # this preserves position when number gets larger or changes plus/minus sign
        step_index = len(text) - position
        # if cursor is at end, edit first digit
        step_index = max(1, step_index)
        return step_index

    def step_exponent(self, step_index):
        # convert cursor position to exponent
        exponent = step_index - 1
        return exponent

    def step_index_to_position(self, step_index, text):
        position = len(text) - step_index
        return position

    def strip_padding(self):
        value = self.value
        self.value = value  # emit signal
        if int(value) == value:
            value = int(value)
        self.setText(str(value))


class FloatLineEdit(IntLineEdit):
    value_changed = QtCore.Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        validator = DoubleValidator()
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)

    def setDecimals(self, decimals):
        self.validator().setDecimals(decimals)

    @IntLineEdit.value.getter
    def value(self):
        try:
            return float(self.text())
        except ValueError:
            return float(0)

    def step_index(self, text, position):
        # get step index relative to decimal point
        # this preserves position when number gets larger or changes plus/minus sign
        decimal_index = text.find('.')
        if decimal_index == -1:
            step_index = len(text) - position
        else:
            step_index = decimal_index - position
        return step_index

    def step_exponent(self, step_index):
        # convert cursor position to exponent
        exponent = step_index
        # if cursor is on the decimal then edit the first decimal
        if step_index >= 0:
            exponent = step_index - 1

        return exponent

    def match_value_to_text(self, value, text, exponent):
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

        # padding_int needs to contain both padding for in and decimals
        padding_int += padding_decimal + 1 * bool(padding_decimal)

        value = round(value, padding_decimal)
        text = f'{value:0{padding_int}.{padding_decimal}f}'

        return text

    def step_index_to_position(self, step_index, text):
        decimal_index = text.find('.')
        position = len(text) - step_index
        if decimal_index > -1:
            # if position is on decimal point, move to first decimal
            if step_index == 0:
                step_index = -1
            position = decimal_index - step_index
        return position

    def setMinimum(self, minimum):
        minimum = minimum or -float('inf')
        self.validator().setBottom(minimum)

    def setMaximum(self, maximum):
        maximum = maximum or float('inf')
        self.validator().setTop(maximum)


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
    ):
        super().__init__(orientation, parent)
        self.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self._slider_min = self.minimum()
        self._slider_max = self.maximum()

    def _exponent(self):
        # automatically adjust step size and tick interval based on slider range
        num_range = abs(self._slider_max - self._slider_min)
        exponent = math.log10(num_range)

        # round exponent up or down with weighting towards down
        if exponent % 1 > 0.8:
            exponent = math.ceil(exponent)
        else:
            exponent = math.floor(exponent)
        return exponent

    def _update_steps(self):
        step = pow(10, max(self._exponent() - 2, 0))

        self.setSingleStep(step)
        self.setPageStep(step * 10)
        self.setTickInterval(step * 10)

    def setMinimum(self, value: int) -> None:
        super().setMinimum(value)
        self._slider_min = value
        self._update_steps()

    def setMaximum(self, value: int) -> None:
        super().setMaximum(value)
        self._slider_max = value
        self._update_steps()


class FloatSlider(IntSlider):
    valueChanged = QtCore.Signal(float)

    def __init__(
        self,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(orientation, parent)
        super().valueChanged.connect(lambda: self.valueChanged.emit(self.value()))

        self._slider_min = self.minimum()
        self._slider_max = self.maximum()

        self.setSingleStep(1)
        self.setPageStep(10)
        self.setTickInterval(10)

    def _update_steps(self):
        # find a value that brings the float range into an int range
        # with step size locked to 1 and 10
        normalize = pow(10, -(self._exponent() - 2))
        QtWidgets.QSlider.setMinimum(self, self._slider_min * normalize)
        QtWidgets.QSlider.setMaximum(self, self._slider_max * normalize)

    def setMinimum(self, value: int) -> None:
        self._slider_min = value
        self._update_steps()

    def setMaximum(self, value: int) -> None:
        self._slider_max = value
        self._update_steps()

    def value(self):
        value = super().value()
        # convert from int slider scale to float
        slider_range = self.maximum() - self.minimum()
        percentage = (value - self.minimum()) / slider_range
        float_value = (
            self._slider_min + (self._slider_max - self._slider_min) * percentage
        )
        return float_value

    def setSliderPosition(self, value: int) -> None:
        # convert from float to int in slider scale
        percentage = (value - self._slider_min) / (self._slider_max - self._slider_min)
        slider_range = self.maximum() - self.minimum()
        clamped_value = min(max(percentage, 0), 1) * slider_range + self.minimum()
        int_value = int(clamped_value)
        super().setSliderPosition(int_value)


class LinkButton(QtWidgets.QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)

        icon = MaterialIcon('link')
        self.setIcon(icon)
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        icon_size = QtCore.QSize(size, size)
        self.setMaximumSize(icon_size)
        self.setCheckable(True)


class ResizeGrip(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.can_resize_vertical = True
        self.can_resize_horizontal = False

        self._resizing = False
        self._start_position = QtCore.QPoint()
        self._start_size = QtCore.QSize()
        self._min_size = None

        self.setCursor(QtCore.Qt.SizeFDiagCursor)
        self.reset()
        parent.installEventFilter(self)

    @property
    def min_size(self):
        if self._min_size is None:
            min_size = self.parent().minimumSize()
            min_size_hint = self.parent().minimumSizeHint()
            min_width = max(min_size.width(), min_size_hint.width(), self.width())
            min_height = max(min_size.height(), min_size_hint.height(), self.height())
            self._min_size = QtCore.QSize(min_width, min_height)
        return self._min_size

    @min_size.setter
    def min_size(self, value):
        self._min_size = value

    def changeEvent(self, event: QtCore.QEvent) -> None:
        if event.type() == QtCore.QEvent.ParentChange and self.parent():
            self.reset()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Resize and obj == self.parent():
            self.reposition()
            self.resize_scroll_bars()
            return False
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        opt = QtWidgets.QStyleOptionSizeGrip()
        opt.initFrom(self)
        opt.corner = QtCore.Qt.BottomRightCorner
        self.style().drawControl(QtWidgets.QStyle.CE_SizeGrip, opt, painter, self)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.reset()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._resizing = True
        self._start_size = self.parent().geometry().size()
        self._start_position = event.globalPos()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._resizing:
            delta = event.globalPos() - self._start_position
            if self.can_resize_horizontal:
                width = self._start_size.width() + delta.x()
                width = max(width, self.min_size.width())
                self.parent().setFixedWidth(width)

            if self.can_resize_vertical:
                height = self._start_size.height() + delta.y()
                height = max(height, self.min_size.height())
                self.parent().setFixedHeight(height)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._resizing = False

    def reset(self):
        size = self.parent().style().pixelMetric(QtWidgets.QStyle.PM_SizeGripSize)
        self.setFixedSize(size, size)
        policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        self.parent().setSizePolicy(policy)
        self.parent().setMinimumSize(self.parent().minimumSizeHint())
        self.min_size = None

    def reposition(self):
        geometry = self.geometry()
        geometry.moveBottomRight(self.parent().contentsRect().bottomRight())
        self.setGeometry(geometry)

    def resize_scroll_bars(self):
        if isinstance(self.parent(), QtWidgets.QAbstractScrollArea):
            size = self.parent().contentsRect().size() - self.size()
            self.parent().horizontalScrollBar().setMaximumWidth(size.width())
            self.parent().verticalScrollBar().setMaximumHeight(size.height())


def main():
    import sys
    import logging
    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    widget = QtWidgets.QWidget()
    widget.setLayout(QtWidgets.QVBoxLayout())

    int_property = IntProperty('int')
    int_property.value = 9
    int_property.slider_max = 50
    widget.layout().addWidget(int_property)

    float_property = FloatProperty('float')
    float_property.decimals = 2
    float_property.value = 13.5234
    widget.layout().addWidget(float_property)

    string_property = StringProperty('string')

    string_property.value = 'asd'
    string_property.area = True
    widget.layout().addWidget(string_property)

    path_property = PathProperty('path')
    path_property.value = 'asd'
    path_property.method = PathProperty.Method.EXISTING_DIR
    widget.layout().addWidget(path_property)

    widget.layout().addWidget(ColorProperty('color'))

    point_property = PointProperty('point')
    widget.layout().addWidget(point_property)

    widget.layout().addWidget(PointFProperty('pointf'))

    size_property = SizeProperty('size')
    size_property.value = QtCore.QSize(17, 56)
    widget.layout().addWidget(size_property)

    widget.layout().addWidget(SizeFProperty('sizef'))

    widget.layout().addWidget(BoolProperty('bool'))

    #  widget.layout().addWidget(
    #     EnumProperty('enum', enum=enum.Enum('Number', ('one', 'two', 'three')))
    # )

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
