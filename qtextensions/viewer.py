import colorsys
import dataclasses
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
        if color is not None:
            r, g, b, a = color.getRgbF()
            rgb = (
                f'<font color="#ff2222">{r:.4f}</font> '
                f'<font color="#00ff22">{g:.4f}</font> '
                f'<font color="#0088ff">{b:.4f}</font>'
            )
            h, s, v, a = color.getHsvF()
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


class ToolBar(QtWidgets.QToolBar):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)


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

        self._init_ui()

    def _init_ui(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.toolbar = self._init_toolbar()
        self.layout().addWidget(self.toolbar)

        # view
        self.scene = GraphicsScene()
        self.scene.background_color = self.background_color

        self.view = GraphicsView()
        self.view.setScene(self.scene)
        self.view.zoom_changed.connect(self.zoom_changed)
        self.layout().addWidget(self.view)

        self.footer = Footer()
        self.footer.background_color = self.background_color
        self.layout().addWidget(self.footer)

        self.view.pixel_position_changed.connect(self.footer.update_pixel_position)
        self.view.pixel_color_changed.connect(self.footer.update_pixel_color)
        self.view.position_changed.connect(self.position_changed.emit)

    def _init_toolbar(self) -> QtWidgets.QToolBar:
        toolbar = QtWidgets.QToolBar()

        size = self.style().pixelMetric(QtWidgets.QStyle.PM_SmallIconSize)
        toolbar.setIconSize(QtCore.QSize(size, size))

        # exposure
        exposure_slider = FloatProperty(parent=toolbar)
        exposure_slider.slider_min = -10
        exposure_slider.slider_max = 10
        exposure_slider.value_changed.connect(self.update_exposure)
        palette = exposure_slider.slider.palette()
        palette.setColor(QtGui.QPalette.Highlight, palette.color(QtGui.QPalette.Base))
        exposure_slider.slider.setPalette(palette)
        toolbar.addWidget(exposure_slider)

        # refresh
        icon = MaterialIcon('refresh')
        refresh_action = QtWidgets.QAction(icon, 'refresh', self)
        refresh_action.triggered.connect(self.refreshed.emit)
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
        # self.zoom_cmb.current
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

    # def connect_ui(self) -> None:
    #     self.exposure_slider.valueChanged.connect(self.exposure_changed)
    #     self.refresh_btn.clicked.connect(self.refresh)
    #     self.pause_btn.clicked.connect(self.pause)
    #     self.zoom_cmb.currentIndexChanged.connect(self.zoom_index_changed)
    #

    def update_exposure(self, value: float) -> None:
        if self.scene.item:
            self.scene.item.exposure = value * 0.25

    # def refresh(self) -> None:
    #     self.refreshed.emit()

    def pause(self, state=True) -> None:
        self.paused = state
        self.pause_changed.emit(self.paused)

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

    def zoom_index_changed(self, index: int) -> None:
        if self.zoom_cmb.currentText() == 'fit':
            self.view.fit()
        elif index > 0:
            self.view.zoom(self.zoom_cmb.currentData())

    def zoom_changed(self, factor: float) -> None:
        self.zoom_cmb.setCurrentIndex(-1)
        self.zoom_cmb.setPlaceholderText(f'{factor:2.1%}')

    # def update_buffer(self, buffer):
    #     self._item.array = buffer
    #     height, width, channels = buffer.shape
    #     self.update_resolution(width, height)
    #
    # def update_resolution(self, x, y):
    #     self.resolution_lbl.setText(f'{x:.0f}x{y:.0f}')
    #     self.resolution = Int2(x, y)
    #
    #     # TODO: Just end yourself you garbage human being
    #     if self._frame:
    #         rect = QtCore.QRectF(0, 0, self.resolution.x, self.resolution.y)
    #         self._frame.setRect(rect)
    #
    # def update_position(self, position):
    #     position.y = self.resolution.y - position.y
    #     self.position_changed.emit(position)


class GraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._background_color = None

        # item
        self.item = GraphicsItem()
        self.addItem(self.item)

        # bounding box frame
        rect = QtCore.QRect()
        color = self.palette().color(QtGui.QPalette.Midlight)
        pen = QtGui.QPen(color)
        pen.setStyle(QtCore.Qt.DotLine)
        pen.setWidth(0)
        brush = QtGui.QBrush()
        brush.setStyle(QtCore.Qt.NoBrush)

        self._frame = self.addRect(rect, pen, brush)

    def update_frame(self) -> None:
        if self.item is None:
            return
        rect = QtCore.QRect(QtCore.QPoint(), self.item.resolution)
        self._frame.setRect(rect)

    @property
    def background_color(self) -> QtGui.QColor:
        return self._background_color

    @background_color.setter
    def background_color(self, value: QtGui.QColor) -> None:
        self._background_color = value
        self.setBackgroundBrush(QtGui.QBrush(value))


class GraphicsView(QtWidgets.QGraphicsView):
    zoom_changed = QtCore.Signal(float)
    position_changed = QtCore.Signal(QtCore.QPoint)
    pixel_position_changed = QtCore.Signal(QtCore.QPoint)
    pixel_color_changed = QtCore.Signal(QtGui.QColor)

    # initialize a 16k scene rect
    scene_rect = QtCore.QRect(-(2**13), -(2**13), 2**14, 2**14)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._dragging = False
        self._item: QtWidgets.QGraphicsItem | None = None

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

        if self._item:
            position = self.mapToScene(event.pos())
            resolution = self._item.boundingRect().size()
            position.setY(resolution.height() - position.y())

            if self._dragging:
                self.position_changed.emit(position)

            color = self._item.color_at(position)
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
        if self._item:
            self.fitInView(self._item, QtCore.Qt.KeepAspectRatio)
            self.zoom_changed.emit(self.absolute_scale)

    def setScene(self, scene: GraphicsScene) -> None:
        super().setScene(scene)
        self._item = scene.item


class GraphicsItem(QtWidgets.QGraphicsItem):
    # TODO: not sure if bad idea:
    # converting to pixmap is slower but on every drag/zoom we are repainting
    # however when changing sliders, we might prefer faster I/O

    def __init__(self, parent: QtWidgets.QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self._exposure = 0
        self._array = None
        self.image = None

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:
        painter.drawImage(option.rect, self.image)

    def boundingRect(self) -> QtCore.QRectF:
        if self.image:
            rect = QtCore.QRectF(self.image.rect())
        else:
            rect = QtCore.QRectF()
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
        if self.array:
            gain = pow(2, self.exposure)
            self.image = image_from_buffer(self.array * gain)

    def color_at(self, position: QtCore.QPoint) -> QtGui.QColor | None:
        if self.array:
            height, width, channels = self.array.shape
            x = position.x()
            y = position.y()
            if x < 0 or x >= width or y < 0 or y >= height:
                return None
            else:
                rgb = self.array[y, x]
                return QtGui.QColor.fromRgbF(*rgb)


def image_from_buffer(buffer: np.ndarray) -> QtGui.QImage:
    # TODO: check speed on [:3]
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

    # buffer = np.tile(np.linspace(0, 1, 512), (512, 1))
    # buffer = np.dstack((buffer, buffer, buffer))
    # viewer.update_buffer(buffer)

    viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
