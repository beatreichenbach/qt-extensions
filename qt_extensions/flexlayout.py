import logging
import sys
import re
import os
import random
from dataclasses import dataclass

from PySide2 import QtWidgets, QtCore, QtGui


class ThumbnailLabel(QtWidgets.QLabel):
    def __init__(self, pixmap, min_size=None, parent=None):
        super().__init__(parent)

        self.pixmap = pixmap

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor('black'))
        self.setPalette(palette)

        if min_size is None:
            min_size = QtCore.QSize(10, 10)

        self.min_size_hint = QtCore.QSize(min_size.width(), min_size.height())
        self.size_hint = QtCore.QSize(min_size.width(), min_size.height())

    def resizeEvent(self, event):
        pixmap = self.pixmap.scaledToWidth(self.size().width())
        self.size_hint = QtCore.QSize(self.min_size_hint.width(), pixmap.size().height())
        self.setPixmap(pixmap)

    def minimumSizeHint(self):
        return self.min_size_hint

    def sizeHint(self):
        return self.size_hint


class ThumbnailWidget(QtWidgets.QFrame):
    background_color = QtGui.QColor(0, 0, 0)

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name

        self.init_ui()

    def init_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        # self.layout().setContentsMargins(4, 4, 4, 4)

        pixmap = QtGui.QPixmap(r'D:\files\dev\027_flare\flare\designer\starburst.png')
        self.image_lbl = ThumbnailLabel(pixmap, QtCore.QSize(random.randrange(50, 200), random.randrange(50, 200)))

        self.layout().addWidget(self.image_lbl)

        self.name_lbl = QtWidgets.QLabel(self.name)
        metrics = QtGui.QFontMetrics(self.name_lbl.font())
        elided_text = metrics.elidedText(self.name, QtCore.Qt.ElideRight, 100)
        self.name_lbl.setText(elided_text)

        self.layout().addWidget(self.name_lbl)

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, palette.color(QtGui.QPalette.Dark))
        palette.setColor(QtGui.QPalette.WindowText, palette.color(QtGui.QPalette.BrightText))
        self.setPalette(palette)

        # actions
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        action = QtWidgets.QAction('Load Preset', parent=self)
        action.triggered.connect(self.load)
        self.addAction(action)
        action = QtWidgets.QAction('Rename Preset', parent=self)
        action.triggered.connect(self.rename)
        self.addAction(action)
        action = QtWidgets.QAction('Delete Preset', parent=self)
        action.triggered.connect(self.delete)
        self.addAction(action)

    def load(self):
        logging.debug('load')

    def rename(self):
        logging.debug('rename')

    def delete(self):
        logging.debug('delete')


class FlexLayout(QtWidgets.QLayout):
    justify_content = 'start'
    align_items = 'stretch'
    item_grow = True
    # align_content = 'None'
    # flex_direction = None
    wrap = True

    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(0, 0, 0, 0)

        self.items = []
        self.height = 0

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]

    def takeAt(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        size = size.grownBy(self.contentsMargins())

        return size

    def _do_layout(self, rect):
        rect = rect.marginsRemoved(self.contentsMargins())
        x = rect.x()
        y = rect.y()
        max_height = 0
        group_width = 0
        spacing = self.spacing()

        group_items = []
        for i, item in enumerate(self.items):
            group_items.append(item)
            next_x = x + item.sizeHint().width() + spacing
            max_height = max(max_height, item.sizeHint().height())
            group_width += item.sizeHint().width() + spacing
            x = next_x

            try:
                next_next_x = next_x + self.items[i + 1].sizeHint().width()
            except IndexError:
                next_next_x = next_x - spacing

            is_last_item = (i == len(self.items) - 1)
            is_overlapped = next_next_x > rect.right()

            if self.wrap:
                end_group = is_overlapped or is_last_item
            else:
                end_group = is_last_item

            if end_group:
                count = len(group_items)
                item_spacing = spacing
                group_width -= spacing

                if self.item_grow or self.justify_content == 'start':
                    item_x = rect.x()
                elif self.justify_content == 'end':
                    item_x = rect.right() - group_width
                elif self.justify_content == 'center':
                    total_space = rect.width() - group_width
                    item_x = rect.x() + total_space / 2
                elif self.justify_content == 'space-between':
                    total_space = rect.width() - group_width + (count - 1) * spacing
                    item_x = rect.x()
                    item_spacing = total_space / max(1, count - 1)

                item_width = (rect.width() - (count - 1) * spacing) / count

                for group_item in group_items:
                    size = group_item.sizeHint()
                    item_height = size.height()

                    if self.align_items == 'start':
                        item_y = y
                    if self.align_items == 'end':
                        item_y = y + max_height - size.height()
                    if self.align_items == 'center':
                        item_y = y + (max_height - size.height()) / 2
                    if self.align_items == 'stretch':
                        item_y = y
                        item_height = max_height

                    if self.item_grow:
                        pass
                        # if count == 1:
                        #     item_width = size.width()
                    else:
                        item_width = size.width()

                    group_item.setGeometry(QtCore.QRect(QtCore.QPoint(item_x, item_y), QtCore.QSize(item_width, item_height)))
                    item_x += item_width + item_spacing

                x = rect.x()
                y = y + max_height + spacing

                max_height = 0
                group_items = []
                group_width = 0

        rect.setBottom(y - spacing)
        rect = rect.marginsAdded(self.contentsMargins())
        self.height = rect.height()


class ThumbnailBrowser(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        self.setLayout(FlexLayout())

        for i in range(5):
            thumbnail = ThumbnailWidget(f'Thumbnail {i}')
            # thumbnail.setMaximumHeight(100)
            self.layout().addWidget(thumbnail)


def main():
    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    path = r'D:\files\dev\027_flare\flare\presets'
    widget = ThumbnailBrowser()
    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
