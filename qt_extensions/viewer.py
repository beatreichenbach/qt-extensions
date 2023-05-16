import typing

import numpy as np
from PySide2 import QtWidgets, QtGui, QtCore

from qt_extensions.combobox import QComboBox
from qt_extensions.icons import MaterialIcon
from qt_extensions.parameters import FloatParameter


def image_from_array(array: np.ndarray) -> QtGui.QImage:
    # TODO: profile this

    array = np.clip(array, 0, 1)
    array = array * 255
    array = array.astype(np.uint8)

    height, width, channels = array.shape
    bytes_per_line = width * channels
    image_format = QtGui.QImage.Format_BGR888
    image = QtGui.QImage(array.data, width, height, bytes_per_line, image_format)
    image = image.rgbSwapped()

    return image


def convert_array(array: np.ndarray) -> np.ndarray:
    # checks whether the array has either 1, 3 or 4 channels and converts
    # it to a 3 channel array while this is the only supported format

    # TODO: this whole function would be nice to turn into some sort of a type hint
    # so that it is clear that functions expect an image like array.
    # TODO: this needs to be done smarter, i shouldn't have to even convert shit here

    if len(array.shape) == 2:
        array = np.dstack((array, array, array))
        return array
    if len(array.shape) == 3:
        if array.shape[2] > 3:
            array = array[:, :, :3]
            return array
        elif array.shape[2] == 3:
            return array
        elif array.shape[2] == 1:
            array = np.dstack((array[:, :, 0], array[:, :, 0], array[:, :, 0]))
            return array
    raise ValueError('Expected numpy array with either 1, 3 or 4 channels.')


class GraphicsItem(QtWidgets.QGraphicsItem):
    def __init__(self, parent: QtWidgets.QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self._exposure: float = 0
        self._array = np.ndarray((0, 0, 3), np.float32)
        self.image = QtGui.QImage()
        self.post_processes: list[typing.Callable[[np.ndarray], np.ndarray]] = [
            self._expose
        ]

    @property
    def array(self) -> np.ndarray:
        return self._array

    @array.setter
    def array(self, value: np.ndarray) -> None:
        array = convert_array(value)
        self._array = array
        self.update_image()

    @property
    def exposure(self) -> float:
        return self._exposure

    @exposure.setter
    def exposure(self, value: float) -> None:
        self._exposure = value
        self.update_image()

    def boundingRect(self) -> QtCore.QRectF:
        rect = QtCore.QRectF(self.image.rect())
        return rect

    def color_at(self, position: QtCore.QPoint) -> QtGui.QColor:
        height, width = self.array.shape[:2]
        x = position.x()
        y = position.y()
        if x < 0 or x >= width or y < 0 or y >= height:
            color = QtGui.QColor()
            color.convertTo(QtGui.QColor.Invalid)
        else:
            rgb = self.array[y, x]
            color = QtGui.QColor.fromRgbF(*rgb)
        return color

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:
        painter.drawImage(option.rect, self.image)

    def update_image(self) -> None:
        array = self.array.copy()
        for post_process in self.post_processes:
            array = post_process(array)
        self.image = image_from_array(array)
        self.update()

    def _expose(self, array: np.ndarray) -> np.ndarray:
        gain = pow(2, self.exposure)
        array = array * gain
        return array


class GraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._background_color = QtGui.QColor(0, 0, 0)
        self._item: GraphicsItem | None = None

        # bounding box frame
        rect = QtCore.QRect()
        color = self.palette().color(QtGui.QPalette.Midlight)
        pen = QtGui.QPen(color)
        pen.setStyle(QtCore.Qt.DotLine)
        pen.setWidth(0)
        brush = QtGui.QBrush()
        brush.setStyle(QtCore.Qt.NoBrush)

        self._frame = self.addRect(rect, pen, brush)
        self._frame.setZValue(1)

    @property
    def background_color(self) -> QtGui.QColor:
        return self._background_color

    @background_color.setter
    def background_color(self, value: QtGui.QColor) -> None:
        self._background_color = value
        self.setBackgroundBrush(QtGui.QBrush(value))

    @property
    def item(self) -> GraphicsItem:
        return self._item

    @item.setter
    def item(self, value: GraphicsItem) -> None:
        if self._item and self._item.parent() == self:
            self.removeItem(self._item)
        self._item = value
        self.addItem(value)

    def update_frame(self, resolution: QtCore.QSize) -> None:
        rect = QtCore.QRect(QtCore.QPoint(), resolution)
        self._frame.setRect(rect)


class GraphicsView(QtWidgets.QGraphicsView):
    zoom_changed = QtCore.Signal(float)
    position_changed = QtCore.Signal(QtCore.QPoint)
    pixel_position_changed = QtCore.Signal(QtCore.QPoint)
    pixel_color_changed = QtCore.Signal(QtGui.QColor)

    # initialize a 16k scene rect
    scene_rect = QtCore.QRect(-(2**13), -(2**13), 2**14, 2**14)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._dragging: bool = False

        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setDragMode(self.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSceneRect(self.scene_rect)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.viewport().setCursor(QtCore.Qt.CrossCursor)

    @property
    def absolute_scale(self) -> float:
        # since there will never be rotation, and scale in x and y are the same,
        # m11 can be used as scale
        return self.transform().m11()

    @absolute_scale.setter
    def absolute_scale(self, value):
        self.setTransform(QtGui.QTransform.fromScale(value, value))

    def fit(self) -> None:
        item = self.scene().item
        if item:
            self.fitInView(item, QtCore.Qt.KeepAspectRatio)
            self.zoom_changed.emit(self.absolute_scale)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_F:
            self.fit()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MidButton:
            handmade_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonPress,
                QtCore.QPointF(event.pos()),
                QtCore.Qt.LeftButton,
                event.buttons(),
                QtCore.Qt.KeyboardModifiers(),
            )
            super().mousePressEvent(handmade_event)
            self.viewport().setCursor(QtCore.Qt.CrossCursor)

        if event.button() == QtCore.Qt.LeftButton:
            self._dragging = True
            self.mouseMoveEvent(event)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MidButton:
            release_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonRelease,
                QtCore.QPointF(event.pos()),
                QtCore.Qt.LeftButton,
                event.buttons(),
                QtCore.Qt.KeyboardModifiers(),
            )
            super().mouseReleaseEvent(release_event)
            self.viewport().setCursor(QtCore.Qt.CrossCursor)

        if event.button() == QtCore.Qt.LeftButton:
            self._dragging = False
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        item = self.scene().item
        if item:
            cursor_position = self.mapToScene(event.pos())
            position = QtCore.QPoint(
                np.floor(cursor_position.x()), np.floor(cursor_position.y())
            )
            # get color before inverting y
            color = item.color_at(position)
            position.setY(item.boundingRect().height() - position.y())

            if self._dragging:
                self.position_changed.emit(position)

            self.pixel_color_changed.emit(color)
            self.pixel_position_changed.emit(position)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

        self.zoom_changed.emit(self.absolute_scale)
        event.accept()

    def setScene(self, scene: GraphicsScene) -> None:
        super().setScene(scene)

    def zoom(self, factor: float) -> None:
        if factor == 0:
            self.fit()
        else:
            self.absolute_scale = factor


class Footer(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._background_color = None

        self._init_ui()

        self.background_color = QtGui.QColor(0, 0, 0)

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QHBoxLayout())

        self.setAutoFillBackground(True)

        self.resolution_lbl = QtWidgets.QLabel('resolution')
        self.layout().addWidget(self.resolution_lbl)

        self.layout().addStretch()

        self.coordinates_lbl = QtWidgets.QLabel('coordinates')
        self.layout().addWidget(self.coordinates_lbl)

        self.rgb_lbl = QtWidgets.QLabel('rgb')
        self.layout().addWidget(self.rgb_lbl)

        self.hsv_lbl = QtWidgets.QLabel('hsv')
        self.layout().addWidget(self.hsv_lbl)

    @property
    def background_color(self) -> QtGui.QColor:
        return self._background_color

    @background_color.setter
    def background_color(self, value: QtGui.QColor) -> None:
        self._background_color = value
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, value)
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
        self.setPalette(palette)

    def update_pixel_color(self, color: QtGui.QColor | None) -> None:
        if color.isValid():
            r, g, b, a = color.getRgbF()
            rgb = (
                f'<font color="#ff2222">{r:.4f}</font> '
                f'<font color="#00ff22">{g:.4f}</font> '
                f'<font color="#0088ff">{b:.4f}</font>'
            )
            h, s, v, a = color.getHsvF()
            h = max(h, 0)
        else:
            rgb = ''
            h, s, v = 0, 0, 0
        hsv = f'H: {h:.2f} S: {s:.2f} V: {v:.2f}'

        self.rgb_lbl.setText(rgb)
        self.hsv_lbl.setText(hsv)

    def update_pixel_position(self, position: QtCore.QPoint | None) -> None:
        if position is not None:
            coordinates = f'x={position.x()} y={position.y()}'
        else:
            coordinates = ''
        self.coordinates_lbl.setText(coordinates)

    def update_resolution(self, resolution: QtCore.QSize) -> None:
        text = f'{resolution.width():.0f}x{resolution.height():.0f}'
        self.resolution_lbl.setText(text)


class ToolBar(QtWidgets.QToolBar):
    refreshed: QtCore.Signal = QtCore.Signal()
    paused: QtCore.Signal = QtCore.Signal(bool)
    exposure_changed: QtCore.Signal = QtCore.Signal(float)
    zoom_changed: QtCore.Signal = QtCore.Signal(float)

    pause_color = QtGui.QColor(217, 33, 33)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._zoom = 0
        self._exposure = 0
        self._exposure_cache = 0

        self._init_actions()

    def _init_actions(self) -> None:
        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        self.setIconSize(QtCore.QSize(size, size))

        # exposure toggle
        icon = MaterialIcon('toggle_on')
        icon_off = MaterialIcon('toggle_off')
        palette = self.palette()
        color = palette.color(QtGui.QPalette.Highlight)
        pixmap = icon_off.pixmap(0, QtGui.QIcon.Active, QtGui.QIcon.On, color)
        icon.addPixmap(pixmap, QtGui.QIcon.Active, QtGui.QIcon.On)

        self.exposure_toggle_action = QtWidgets.QAction(icon, 'exposure_toggle', self)
        self.exposure_toggle_action.setCheckable(True)
        self.exposure_toggle_action.toggled.connect(self._exposure_toggle)
        self.addAction(self.exposure_toggle_action)

        # exposure slider
        self.exposure_slider = FloatParameter(parent=self)
        self.exposure_slider.slider_min = -10
        self.exposure_slider.slider_max = 10
        self.exposure_slider.value_changed.connect(self._exposure_change)
        palette = self.exposure_slider.slider.palette()
        palette.setColor(QtGui.QPalette.Highlight, palette.color(QtGui.QPalette.Base))
        self.exposure_slider.slider.setPalette(palette)

        exposure_action = QtWidgets.QWidgetAction(self)
        exposure_action.setText('exposure')
        exposure_action.setDefaultWidget(self.exposure_slider)
        self.addAction(exposure_action)

        # refresh
        icon = MaterialIcon('refresh')
        refresh_action = QtWidgets.QAction(icon, 'refresh', self)
        refresh_action.triggered.connect(self.refreshed.emit)
        self.addAction(refresh_action)

        # pause
        icon = MaterialIcon('pause')
        color = self.pause_color
        pixmap = icon.pixmap(0, QtGui.QIcon.Active, QtGui.QIcon.On, color)
        icon.addPixmap(pixmap, QtGui.QIcon.Active, QtGui.QIcon.On)
        pause_action = QtWidgets.QAction(icon, 'pause', self)
        pause_action.setCheckable(True)
        pause_action.toggled.connect(self.paused.emit)
        self.addAction(pause_action)

        # zoom
        self.zoom_cmb = QComboBox()
        self.zoom_cmb.addItem('fit')
        factors = [0.10, 0.25, 0.33, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5]
        for factor in reversed(factors):
            self.zoom_cmb.addItem(f'{factor:2.0%}', factor)
        self.zoom_cmb.setMaxVisibleItems(self.zoom_cmb.count())
        self.zoom_cmb.currentIndexChanged.connect(self._zoom_index_change)

        # currently AdjustToContents doesn't do anything, but this might be because
        # the placeholder text is broken, thus setting minimContentsLength works for
        # ensuring that the full placeholder text is visible.
        self.zoom_cmb.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.zoom_cmb.setMinimumContentsLength(6)

        zoom_action = QtWidgets.QWidgetAction(self)
        zoom_action.setText('zoom')
        zoom_action.setDefaultWidget(self.zoom_cmb)
        self.addAction(zoom_action)

        # proxy resolution
        # proxy_items = OrderedDict()
        # for i in range(6):
        #     ratio = 2**i
        #     proxy_items[f'1:{ratio}'] = ratio
        # proxy_enum = Enum('Proxy_Resolution', proxy_items)
        # self.proxy_cmb = EnumProperty(
        #     name='proxy',
        #     enum=proxy_enum
        #     )
        # header_lay.addWidget(self.proxy_cmb)

    @property
    def exposure(self) -> float:
        return self._exposure

    @exposure.setter
    def exposure(self, value: float) -> None:
        self._exposure = value
        self.exposure_slider.value = value

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = value
        self.zoom_cmb.setCurrentIndex(-1)
        self.zoom_cmb.setPlaceholderText(f'{value:2.1%}')

    def find_action(self, text: str) -> QtWidgets.QAction | None:
        for action in self.actions():
            if action.text() == text:
                return action

    def _exposure_change(self, value: float) -> None:
        self.exposure_toggle_action.blockSignals(True)
        self.exposure_toggle_action.setChecked(value != 0)
        self.exposure_toggle_action.blockSignals(False)

        self._exposure = value
        if value != 0:
            self._exposure_cache = value
        self.exposure_changed.emit(value)

    def _exposure_toggle(self, value: bool) -> None:
        if self.exposure != 0:
            self.exposure = 0
        else:
            self.exposure = self._exposure_cache

    def _zoom_index_change(self, index: int) -> None:
        if self.zoom_cmb.currentText() == 'fit':
            self._zoom = 0
        elif index > 0:
            self._zoom = self.zoom_cmb.currentData()
        else:
            return
        self.zoom_changed.emit(self._zoom)


class Viewer(QtWidgets.QWidget):
    # https://cyrille.rossant.net/a-tutorial-on-openglopencl-interoperability-in-python/
    # Using OpenGL/OpenCL interoperability is currently not feasible as pyopencl
    # needs to be built with opengl support. There is no pip package with it enabled

    refreshed: QtCore.Signal = QtCore.Signal()
    pause_changed: QtCore.Signal = QtCore.Signal(bool)
    position_changed: QtCore.Signal = QtCore.Signal(QtCore.QPoint)

    background_color = QtGui.QColor(0, 0, 0)
    pause_color = QtGui.QColor(217, 33, 33)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.paused = False
        self._post_processes = []
        self._resolution = QtCore.QSize()

        self._init_ui()

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # toolbar
        self.toolbar = ToolBar()
        self.toolbar.pause_color = self.pause_color
        self.toolbar.refreshed.connect(self.refresh)
        self.toolbar.paused.connect(self.pause)
        self.toolbar.exposure_changed.connect(self._exposure_change)
        self.toolbar.zoom_changed.connect(self._toolbar_zoom_change)
        self.layout().addWidget(self.toolbar)

        # view
        self.scene = GraphicsScene()
        self.scene.background_color = self.background_color

        self.item = GraphicsItem()
        self.scene.item = self.item

        self.view = GraphicsView()
        self.view.setScene(self.scene)
        self.view.zoom_changed.connect(self._view_zoom_change)
        self.view.fit()
        self.layout().addWidget(self.view)

        # footer
        self.footer = Footer()
        self.footer.background_color = self.background_color
        self.layout().addWidget(self.footer)

        # signals
        self.view.pixel_position_changed.connect(self.footer.update_pixel_position)
        self.view.pixel_color_changed.connect(self.footer.update_pixel_color)
        self.view.position_changed.connect(self.position_changed.emit)

    @property
    def resolution(self) -> QtCore.QSize:
        return self._resolution

    @resolution.setter
    def resolution(self, value: QtCore.QSize) -> None:
        if self._resolution != value:
            self._resolution = value
            self.footer.update_resolution(value)
            self.scene.update_frame(value)
            self.view.fit()

    @property
    def exposure(self) -> float:
        return self.item.exposure

    @exposure.setter
    def exposure(self, value: float) -> None:
        self.item.exposure = value
        self.toolbar.exposure = value
        self._exposure_change(value)

    def pause(self, state=True) -> None:
        self.paused = state

        if self.paused:
            self.view.setFrameShape(QtWidgets.QFrame.Box)
            self.view.setStyleSheet(
                f'QFrame {{ border: 1px solid {self.pause_color.name()}; }}'
            )
            self.view.setEnabled(False)
        else:
            self.view.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.view.setStyleSheet('')
            self.view.setEnabled(True)

        self.pause_changed.emit(self.paused)

    def state(self) -> dict:
        state = {'exposure': self.exposure}
        return state

    def set_state(self, state: dict) -> None:
        values = {'exposure': 0}
        values.update(state)
        self.exposure = values['exposure']

    def refresh(self) -> None:
        self.refreshed.emit()

    def relative_position(self, position: QtCore.QPoint) -> QtCore.QPointF:
        return QtCore.QPointF(
            (position.x() / self.resolution.width() - 0.5) * 2,
            (position.y() / self.resolution.height() - 0.5) * 2,
        )

    def update_image(self, image: np.ndarray) -> None:
        if not self.paused:
            self.item.array = image
            self.resolution = QtCore.QSize(image.shape[1], image.shape[0])

    def _exposure_change(self, value: float) -> None:
        if not self.paused:
            self.item.exposure = value

    def _toolbar_zoom_change(self, zoom: float) -> None:
        self.view.zoom(zoom)

    def _view_zoom_change(self, zoom: float) -> None:
        self.toolbar.zoom = zoom
