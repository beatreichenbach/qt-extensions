from collections import OrderedDict
import colorsys
from enum import Enum
import logging

import numpy as np
from PySide2 import QtWidgets, QtGui, QtCore


from qtproperties import FloatProperty, EnumProperty, Int2


class Viewer(QtWidgets.QWidget):
    # https://cyrille.rossant.net/a-tutorial-on-openglopencl-interoperability-in-python/
    # Using OpenGL/OpenCL interoperability is currently not feasable as pyopencl
    # needs to be built with opengl support. There is no pip package with it enabled
    refreshed = QtCore.Signal()
    pause_changed = QtCore.Signal(bool)
    position_changed = QtCore.Signal(Int2)

    background_color = QtGui.QColor(0, 0, 0)

    def __init__(self, name='', parent=None):
        super().__init__(parent)

        self.paused = False
        self.item = None
        self.resolution = None
        self.frame = None

        self.init_ui()
        self.connect_ui()

        self.scene = QtWidgets.QGraphicsScene()
        self.scene.setBackgroundBrush(QtGui.QBrush(self.background_color))
        self.main_view.setScene(self.scene)

        # TODO: Kill me now
        buffer = np.zeros((512, 512, 3))
        height, width, channels = buffer.shape
        self.update_resolution(width, height)
        self.item = GraphicsNPArrayItem(buffer)
        self.scene.addItem(self.item)

        rect = QtCore.QRect(0, 0, self.resolution.x, self.resolution.y)
        pen = QtGui.QPen(QtGui.QColor(100, 100, 100))
        pen.setStyle(QtCore.Qt.DotLine)
        pen.setWidth(0)
        brush = QtGui.QBrush()
        brush.setStyle(QtCore.Qt.NoBrush)
        self.frame = self.scene.addRect(rect, pen, brush)

        self.main_view.fit()

    def init_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        # self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        header_lay = QtWidgets.QHBoxLayout()
        header_lay.setSpacing(4)
        self.layout().addLayout(header_lay)
        self.header_layout = header_lay

        # exposure
        self.exposure_slider = FloatProperty(
            name='exposure', slider_min=-10, slider_max=10
        )

        palette = self.exposure_slider.slider.palette()
        palette.setColor(QtGui.QPalette.Highlight, palette.color(QtGui.QPalette.Base))
        self.exposure_slider.slider.setPalette(palette)

        header_lay.setStretch(0, 1)
        header_lay.addWidget(self.exposure_slider)

        # refresh
        self.refresh_btn = QtWidgets.QPushButton()
        icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_BrowserReload
        )
        self.refresh_btn.setIcon(icon)
        header_lay.addWidget(self.refresh_btn)

        # pause
        self.pause_btn = QtWidgets.QPushButton()
        icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_MediaPause
        )
        self.pause_btn.setIcon(icon)
        self.pause_btn.setCheckable(True)
        header_lay.addWidget(self.pause_btn)

        # zoom
        self.zoom_cmb = QComboBox()
        self.zoom_cmb.addItem('fit')
        factors = [0.10, 0.25, 0.33, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5]
        for factor in reversed(factors):
            self.zoom_cmb.addItem(f'{factor:2.0%}', factor)
        self.zoom_cmb.setCurrentText('100%')
        self.zoom_cmb.setMaxVisibleItems(self.zoom_cmb.count())

        header_lay.addWidget(self.zoom_cmb)

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

        # view
        self.main_view = GraphicsView()
        self.main_view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.layout().addWidget(self.main_view)

        footer_wdg = QtWidgets.QWidget()
        footer_wdg.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(footer_wdg)

        footer_wdg.setAutoFillBackground(True)
        palette = footer_wdg.palette()
        palette.setColor(QtGui.QPalette.Window, self.background_color)
        palette.setColor(
            QtGui.QPalette.WindowText, palette.color(QtGui.QPalette.BrightText)
        )
        footer_wdg.setPalette(palette)

        self.resolution_lbl = QtWidgets.QLabel('resolution')
        footer_wdg.layout().addWidget(self.resolution_lbl)
        self.coordinates_lbl = QtWidgets.QLabel('coordinates')
        footer_wdg.layout().addWidget(self.coordinates_lbl)
        self.rgb_lbl = QtWidgets.QLabel('rgb')
        footer_wdg.layout().addWidget(self.rgb_lbl)
        self.hsv_lbl = QtWidgets.QLabel('hsv')
        footer_wdg.layout().addWidget(self.hsv_lbl)

    def connect_ui(self):
        self.exposure_slider.valueChanged.connect(self.exposure_changed)
        self.refresh_btn.clicked.connect(self.refresh)
        self.pause_btn.clicked.connect(self.pause)
        self.zoom_cmb.currentIndexChanged.connect(self.zoom_index_changed)

        self.main_view.zoom_changed.connect(self.zoom_changed)
        self.main_view.pixel_data_changed.connect(self.update_pixel_data)
        self.main_view.position_changed.connect(self.update_position)

    def exposure_changed(self, value):
        if self.item:
            self.item.exposure = value * 0.25

    def refresh(self):
        self.refreshed.emit()

    def pause(self):
        self.paused = not self.paused
        self.pause_changed.emit(self.paused)

        if self.paused:
            self.main_view.setFrameShape(QtWidgets.QFrame.Box)
            self.main_view.setStyleSheet('QFrame { border: 1px solid red; }')
        else:
            self.main_view.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.main_view.setStyleSheet('')

    def zoom_index_changed(self, index: int) -> None:
        if self.zoom_cmb.currentText() == 'fit':
            self.main_view.fit()
        elif index > 0:
            self.main_view.zoom(self.zoom_cmb.currentData())

    def zoom_changed(self, factor: float) -> None:
        self.zoom_cmb.setCurrentIndex(-1)
        self.zoom_cmb.setPlaceholderText(f'{factor:2.1%}')

    def update_buffer(self, buffer):
        self.item.array = buffer
        height, width, channels = buffer.shape
        self.update_resolution(width, height)

    def update_pixel_data(self, pixel_data):
        if pixel_data['position'] is not None:
            x, y = pixel_data['position'].x, pixel_data['position'].y
            coordinates = f'x={x} y={self.resolution.y - y}'
        else:
            coordinates = ''

        if pixel_data['rgb'] is not None:
            r, g, b = pixel_data['rgb']
            rgb = (
                f'<font color="#ff2222">{r:.4f}</font> '
                f'<font color="#00ff22">{g:.4f}</font> '
                f'<font color="#0088ff">{b:.4f}</font>'
            )
        else:
            rgb = ''

        if pixel_data['hsv'] is not None:
            h, s, v = pixel_data['hsv']
        else:
            h, s, v = 0, 0, 0
        hsv = f'H: {h:.2f} S: {s:.2f} V: {v:.2f}'

        self.coordinates_lbl.setText(coordinates)
        self.rgb_lbl.setText(rgb)
        self.hsv_lbl.setText(hsv)

    def update_resolution(self, x, y):
        self.resolution_lbl.setText(f'{x:.0f}x{y:.0f}')
        self.resolution = Int2(x, y)

        # TODO: Just end yourself you garbage human being
        if self.frame:
            rect = QtCore.QRectF(0, 0, self.resolution.x, self.resolution.y)
            self.frame.setRect(rect)

    def update_position(self, position):
        position.y = self.resolution.y - position.y
        self.position_changed.emit(position)


class GraphicsView(QtWidgets.QGraphicsView):
    zoom_changed = QtCore.Signal(float)
    pixel_data_changed = QtCore.Signal(dict)
    position_changed = QtCore.Signal(Int2)
    # TODO: better name
    # This is specifically a class to only display one item (?) and that is a ndarray buffer

    def __init__(self, parent=None):
        super().__init__(parent)

        self.left_button_pressed = False

        self._position = Int2()
        self._pixel_data = {'position': None, 'rgb': None, 'hsv': None}

        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.setDragMode(self.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.viewport().setCursor(QtCore.Qt.CrossCursor)

        # 16k scene
        self.setSceneRect(-(2**13), -(2**13), 2**14, 2**14)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoomOutFactor = 1 / zoom_in_factor

        # save the scene pos
        old_pos = self.mapToScene(event.pos())

        # zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoomOutFactor
        self.scale(zoom_factor, zoom_factor)

        # get the new position
        newPos = self.mapToScene(event.pos())

        # move scene to old position
        delta = newPos - old_pos
        self.translate(delta.x(), delta.y())

        self.zoom_changed.emit(self.absolute_scale)

    def mousePressEvent(self, event):
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
            self.left_button_pressed = True
            self.mouseMoveEvent(event)
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            handmade_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonRelease,
                QtCore.QPointF(event.pos()),
                QtCore.Qt.LeftButton,
                event.buttons(),
                QtCore.Qt.KeyboardModifiers(),
            )
            super().mouseReleaseEvent(handmade_event)
            self.viewport().setCursor(QtCore.Qt.CrossCursor)

        if event.button() == QtCore.Qt.LeftButton:
            self.left_button_pressed = False
            return

        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        position = self.mouse_position(event)
        if self.left_button_pressed:
            self.position = position

        item = self.scene().items()[-1]
        rgb = item.pixel(position.x, position.y)
        hsv = None
        if rgb is not None and (rgb > 0).all():
            hsv = colorsys.rgb_to_hsv(*rgb)
        self.pixel_data = {'position': position, 'rgb': rgb, 'hsv': hsv}

    def mouse_position(self, event):
        point = self.mapToScene(event.pos())
        position = Int2(point.x(), point.y())
        return position

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_F:
            self.fit()
            event.accept()

    @property
    def absolute_scale(self):
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
        # TODO: make nicer
        item = self.scene().items()[-1]
        self.fitInView(item, QtCore.Qt.KeepAspectRatio)
        self.zoom_changed.emit(self.absolute_scale)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.position_changed.emit(value)

    @property
    def pixel_data(self):
        return self._pixel_data

    @pixel_data.setter
    def pixel_data(self, value):
        self._pixel_data = value
        self.pixel_data_changed.emit(value)


class GraphicsNPArrayItem(QtWidgets.QGraphicsItem):
    # TODO: not sure if bad idea:
    # converting to pixmap is slower but on every drag/zoom we are repainting
    # however when changing sliders, we might prefer faster I/O

    def __init__(self, array: np.ndarray) -> None:
        super().__init__()
        self._exposure = 0
        self._array = array
        self.update()

    def paint(self, painter, option, widget):
        painter.drawImage(option.rect, self.image)

    def boundingRect(self):
        return QtCore.QRectF(self.image.rect())

    @property
    def array(self):
        return self._array

    @array.setter
    def array(self, value):
        self._array = value[:, :, :3]
        self.update()

    @property
    def exposure(self):
        return self._exposure

    @exposure.setter
    def exposure(self, value):
        self._exposure = value
        self.update()

    def update(self):
        gain = pow(2, self.exposure)
        self.image = image_from_buffer(self.array * gain)
        super().update()

    def pixel(self, x, y):
        height, width, channels = self.array.shape
        if x < 0 or x >= width or y < 0 or y >= height:
            return None
        else:
            return self.array[y, x]


class QComboBox(QtWidgets.QComboBox):
    def paintEvent(self, event):
        # https://code.qt.io/cgit/qt/qtbase.git/tree/src/widgets/widgets/qcombobox.cpp?h=5.15.2#n3173
        painter = QtWidgets.QStylePainter(self)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))

        # draw the combobox frame, focusrect and selected etc.
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)

        if self.currentIndex() < 0:
            opt.palette.setBrush(
                QtGui.QPalette.ButtonText,
                opt.palette.brush(QtGui.QPalette.ButtonText).color(),
            )
            if self.placeholderText():
                opt.currentText = self.placeholderText()

        # draw the icon and text
        painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt)


def image_from_buffer(buffer):
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
    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)
    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    viewer = Viewer()

    buffer = np.tile(np.linspace(0, 1, 512), (512, 1))
    buffer = np.dstack((buffer, buffer, buffer))
    viewer.update_buffer(buffer)

    viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
