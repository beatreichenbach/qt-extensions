import logging

import numpy as np
from PySide2 import QtWidgets, QtGui, QtCore

from qtextensions.icons import MaterialIcon
from qtextensions.properties import FloatProperty
from qtextensions.combobox import QComboBox


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

    def update_resolution(self, resolution: QtCore.QSize) -> None:
        text = f'{resolution.width():.0f}x{resolution.height():.0f}'
        self.resolution_lbl.setText(text)

    def update_pixel_position(self, position: QtCore.QPoint | None) -> None:
        if position is not None:
            coordinates = f'x={position.x()} y={position.y()}'
        else:
            coordinates = ''
        self.coordinates_lbl.setText(coordinates)

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

    @property
    def background_color(self) -> QtGui.QColor:
        return self._background_color

    @background_color.setter
    def background_color(self, value: QtGui.QColor) -> None:
        self._background_color = value
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, value)
        palette.setColor(
            QtGui.QPalette.WindowText, palette.color(QtGui.QPalette.BrightText)
        )
        self.setPalette(palette)


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
        self._resolution = QtCore.QSize()

        self._init_ui()

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # toolbar
        self.toolbar = self._toolbar()
        self.layout().addWidget(self.toolbar)

        # view
        self.scene = GraphicsScene()
        self.scene.background_color = self.background_color

        self.item = GraphicsItem()
        self.scene.item = self.item

        self.view = GraphicsView()
        self.view.setScene(self.scene)
        self.view.zoom_changed.connect(self.zoom_change)
        self.layout().addWidget(self.view)

        # footer
        self.footer = Footer()
        self.footer.background_color = self.background_color
        self.layout().addWidget(self.footer)

        # signals
        self.view.pixel_position_changed.connect(self.footer.update_pixel_position)
        self.view.pixel_color_changed.connect(self.footer.update_pixel_color)
        self.view.position_changed.connect(self.position_changed.emit)

    def _toolbar(self) -> QtWidgets.QToolBar:
        toolbar = QtWidgets.QToolBar()

        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        toolbar.setIconSize(QtCore.QSize(size, size))

        # exposure
        exposure_slider = FloatProperty(parent=toolbar)
        exposure_slider.slider_min = -10
        exposure_slider.slider_max = 10
        exposure_slider.value_changed.connect(self.exposure_change)
        palette = exposure_slider.slider.palette()
        palette.setColor(QtGui.QPalette.Highlight, palette.color(QtGui.QPalette.Base))
        exposure_slider.slider.setPalette(palette)
        toolbar.addWidget(exposure_slider)

        # refresh
        icon = MaterialIcon('refresh')
        refresh_action = QtWidgets.QAction(icon, 'refresh', self)
        refresh_action.triggered.connect(self.refresh)
        toolbar.addAction(refresh_action)

        # pause
        icon = MaterialIcon('pause')
        color = self.pause_color
        icon.set_color(color, QtGui.QIcon.Active, QtGui.QIcon.On)
        pause_action = QtWidgets.QAction(icon, 'pause', self)
        pause_action.setCheckable(True)
        pause_action.toggled.connect(self.pause)
        toolbar.addAction(pause_action)

        # zoom
        self.zoom_cmb = QComboBox()
        self.zoom_cmb.addItem('fit')
        factors = [0.10, 0.25, 0.33, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5]
        for factor in reversed(factors):
            self.zoom_cmb.addItem(f'{factor:2.0%}', factor)
        self.zoom_cmb.setMaxVisibleItems(self.zoom_cmb.count())
        self.zoom_cmb.currentIndexChanged.connect(self.zoom_index_change)
        toolbar.addWidget(self.zoom_cmb)

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

        return toolbar

    def exposure_change(self, value: float) -> None:
        if not self.paused:
            self.item.exposure = value

    def refresh(self) -> None:
        self.refreshed.emit()

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

    def zoom_index_change(self, index: int) -> None:
        if self.zoom_cmb.currentText() == 'fit':
            self.view.fit()
        elif index > 0:
            self.view.zoom(self.zoom_cmb.currentData())

    def zoom_change(self, factor: float) -> None:
        self.zoom_cmb.setCurrentIndex(-1)
        self.zoom_cmb.setPlaceholderText(f'{factor:2.1%}')

    def update_buffer(self, buffer):
        if not self.paused:
            self.item.array = buffer
            self.resolution = QtCore.QSize(buffer.shape[0], buffer.shape[1])

    @property
    def resolution(self) -> QtCore.QSize:
        return self._resolution

    @resolution.setter
    def resolution(self, value: QtCore.QSize) -> None:
        if self._resolution != value:
            self._resolution = value
            self.footer.update_resolution(value)
            self.scene.update_frame(value)


class GraphicsItem(QtWidgets.QGraphicsItem):
    # TODO: not sure if bad idea:
    # converting to pixmap is slower but on every drag/zoom we are repainting
    # however when changing sliders, we might prefer faster I/O

    def __init__(self, parent: QtWidgets.QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self._exposure: float = 0
        self._array = np.ndarray((0, 0, 3))
        self.image = QtGui.QImage()

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:
        painter.drawImage(option.rect, self.image)

    def boundingRect(self) -> QtCore.QRectF:
        rect = QtCore.QRectF(self.image.rect())
        return rect

    @property
    def array(self) -> np.ndarray:
        return self._array

    @array.setter
    def array(self, value: np.ndarray) -> None:
        self._array = value
        self.update_image()

    @property
    def exposure(self) -> float:
        return self._exposure

    @exposure.setter
    def exposure(self, value: float) -> None:
        self._exposure = value
        self.update_image()

    def update_image(self) -> None:
        gain = pow(2, self.exposure)
        self.image = image_from_buffer(self.array * gain)

    def color_at(self, position: QtCore.QPoint) -> QtGui.QColor:
        height, width, channels = self.array.shape
        x = position.x()
        y = position.y()
        if x < 0 or x >= width or y < 0 or y >= height:
            color = QtGui.QColor()
            color.convertTo(QtGui.QColor.Invalid)
        else:
            rgb = self.array[y, x]
            color = QtGui.QColor.fromRgbF(*rgb)
        return color


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

    def update_frame(self, resolution: QtCore.QSize) -> None:
        rect = QtCore.QRect(QtCore.QPoint(), resolution)
        self._frame.setRect(rect)

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
        self.viewport().setCursor(QtCore.Qt.CrossCursor)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        old_pos = self.mapToScene(event.pos())

        # zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

        new_pos = self.mapToScene(event.pos())

        # move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

        self.zoom_changed.emit(self.absolute_scale)
        event.accept()

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
            position = self.mapToScene(event.pos()).toPoint()
            position.setY(item.boundingRect().height() - position.y())

            if self._dragging:
                self.position_changed.emit(position)

            color = item.color_at(position)
            self.pixel_color_changed.emit(color)
            self.pixel_position_changed.emit(position)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_F:
            self.fit()
            event.accept()
            return
        super().keyPressEvent(event)

    @property
    def absolute_scale(self) -> float:
        # since there will never be rotation, and scale in x and y are the same,
        # m11 can be used as scale
        return self.transform().m11()

    @absolute_scale.setter
    def absolute_scale(self, value):
        self.setTransform(QtGui.QTransform.fromScale(value, value))

    def zoom(self, factor: float) -> None:
        if factor == 0:
            self.fit()
        else:
            self.absolute_scale = factor

    def fit(self) -> None:
        item = self.scene().item
        if item:
            self.fitInView(item, QtCore.Qt.KeepAspectRatio)
            self.zoom_changed.emit(self.absolute_scale)

    def setScene(self, scene: GraphicsScene) -> None:
        super().setScene(scene)


def image_from_buffer(buffer: np.ndarray) -> QtGui.QImage:
    # TODO: check speed on [:3]
    # TODO: overall profile this

    buffer = buffer[:, :, :3]
    buffer = np.clip(buffer, 0, 1)
    buffer *= 255
    buffer = buffer.astype(np.uint8)
    height, width, channels = buffer.shape
    bytes_per_line = 3 * width
    image = QtGui.QImage(
        buffer.data, width, height, bytes_per_line, QtGui.QImage.Format_BGR888
    )
    image = image.rgbSwapped()
    return image


def main():
    import sys
    from qtextensions import theme

    logging.getLogger().setLevel(logging.DEBUG)
    app = QtWidgets.QApplication()
    theme.apply_theme(theme.monokai)

    viewer = Viewer()

    buffer = np.tile(np.linspace(0, 1, 512), (512, 1))
    buffer = np.dstack((buffer, buffer, buffer))
    viewer.update_buffer(buffer)

    viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
