import logging
import sys
import re
import os
import dataclasses
import shutil
from enum import auto, Enum

from PySide2 import QtWidgets, QtCore, QtGui


class FlexItemDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textMargins = QtCore.QMargins(4, 4, 4, 4)

    def paint(self, painter, option, index):
        widget = option.widget
        style = widget.style() or QtWidgets.QApplication.style()

        # draw frame
        option_frame = QtWidgets.QStyleOptionFrame()

        palette = option_frame.palette

        option_frame.palette.setColor(QtGui.QPalette.Window, palette.color(QtGui.QPalette.Dark))

        option_frame.state = option.state
        option_frame.rect = option.rect
        option_frame.rect.adjust(1, 1, -1, -1)
        option_frame.frameShape = QtWidgets.QFrame.StyledPanel
        option_frame.lineWidth = 1

        painter.fillRect(option_frame.rect, palette.color(QtGui.QPalette.Window))

        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        style.drawPrimitive(QtWidgets.QStyle.PE_Frame, option_frame, painter)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # draw decoration and display
        option_view_item = QtWidgets.QStyleOptionViewItem(option)
        option_view_item.state &= ~QtWidgets.QStyle.State_Selected

        super().paint(painter, option_view_item, index)

        # draw selection
        if option.state & QtWidgets.QStyle.State_Selected:
            color = QtCore.Qt.cyan
            color = palette.color(QtGui.QPalette.Highlight)
            pen = QtGui.QPen(color)
            painter.setPen(pen)
            painter.drawRect(option.rect)

        # draw focus
        super().drawFocus(painter, option, option.rect)

    def drawFocus(self, painter, option, rect):
        return

    def drawDecoration(self, painter, option, rect, pixmap):
        option.rect.adjust(2, 2, -2, -2)
        # option.rect.adjust(self.textMargins.left(), self.textMargins.top(), -self.textMargins.right(), 0)

        font_metrics = painter.fontMetrics()
        height = font_metrics.height()
        height += self.textMargins.top() + self.textMargins.bottom()

        rect = QtCore.QRect(option.rect)
        rect.setHeight(option.rect.height() - height)

        if pixmap is None or not rect.isValid():
            return

        pixmap = pixmap.scaled(rect.size(), QtCore.Qt.KeepAspectRatioByExpanding)

        if option.state & QtWidgets.QStyle.State_Selected:
            pixmap = self.selectedPixmap(
                pixmap, option.palette, option.state & QtWidgets.QStyle.State_Enabled)

        source_rect = QtWidgets.QStyle.alignedRect(
            option.direction, option.decorationAlignment, rect.size(), pixmap.rect())

        painter.drawPixmap(rect, pixmap, source_rect)

    def drawDisplay(self, painter, option, rect, text):
        # get maximum
        rect.adjust(self.textMargins.left(), 0, -self.textMargins.right(), -self.textMargins.bottom())
        super().drawDisplay(painter, option, rect, text)

    def sizeHint(self, option, index):
        size_hint = super().sizeHint(option, index)
        return size_hint


class FlexView(QtWidgets.QAbstractItemView):
    flex_direction = None
    align_content = None
    justify_content = 'START'
    align_items = 'STRETCH'
    item = ''
    wrap = True

    min_size = QtCore.QSize()
    default_size = QtCore.QSize()

    # positional flags
    START = auto()
    END = auto()
    CENTER = auto()
    SPACE_BETWEEN = auto()
    SPACE_AROUND = auto()
    SPACE_EVENLY = auto()
    STRETCH = auto()

    # item flags
    NO_GROW = auto()
    GROW = auto()
    MATCH_PREVIOUS = auto()

    # layout flags
    WRAP = auto()
    WRAP_REVERSE = auto()
    ROW = auto()
    ROW_REVERSE = auto()
    COLUMN = auto()
    COLUMN_REVERSE = auto()

    # flex_direction = ROW | (ROW_REVERSE | COLUMN | COLUMN_REVERSE)
    # align_content = START | END | CENTER | SPACE_BETWEEN | (SPACE_AROUND | SPACE_EVENLY)
    # justify_content = START | END | CENTER | SPACE_BETWEEN | (SPACE_AROUND)
    # align_items = START | END | CENTER | STRETCH
    # item = NO_GROW | GROW | MATCH_PREVIOUS
    # wrap = NONE | WRAP | WRAP_REVERSE

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setItemDelegate(FlexItemDelegate())
        self.item_rects = []

        self.contents_margins = QtCore.QMargins(6, 6, 6, 6)
        self.spacing = 6

        self.items = []
        self.height = 0

        self.rubber_band = None
        self.rubber_origin = None

    def update_item_rects(self):
        default_size = QtCore.QSize(250, 150)
        rect = self.viewport().rect()
        rect = rect.marginsRemoved(self.contents_margins)
        x = rect.x()
        y = rect.y()
        max_height = 0
        group_width = 0
        spacing = self.spacing
        self.item_rects = []

        items = range(self.model().rowCount(self.rootIndex()))

        group_items = []
        for i, item in enumerate(items):
            group_items.append(item)
            # max_height = max(max_height, item.sizeHint().height())
            # next_x = x + item.sizeHint().width() + spacing
            # group_width += item.sizeHint().width() + spacing
            max_height = max(max_height, default_size.height())
            next_x = x + default_size.width() + spacing
            group_width += default_size.width() + spacing
            x = next_x

            try:
                # next_next_x = next_x + items[i + 1].sizeHint().width()
                next_next_x = next_x + default_size.width()
            except IndexError:
                next_next_x = next_x - spacing

            is_last_item = (i == len(items) - 1)
            is_overlapped = next_next_x > rect.right()

            if self.wrap:
                end_group = is_overlapped or is_last_item
            else:
                end_group = is_last_item

            if end_group:
                count = len(group_items)
                item_spacing = spacing
                group_width -= spacing

                if self.item == 'GROW' or self.justify_content == 'START':
                    item_x = rect.x()
                elif self.justify_content == 'END':
                    item_x = rect.right() - group_width
                elif self.justify_content == 'CENTER':
                    total_space = rect.width() - group_width
                    item_x = rect.x() + total_space / 2
                elif self.justify_content == 'SPACE-BETWEEN':
                    total_space = rect.width() - group_width + (count - 1) * spacing
                    item_x = rect.x()
                    item_spacing = total_space / max(1, count - 1)

                item_width = (rect.width() - (count - 1) * spacing) / count

                for j, group_item in enumerate(group_items):
                    # size = group_item.sizeHint()
                    size = default_size
                    item_height = size.height()

                    if self.align_items == 'START':
                        item_y = y
                    if self.align_items == 'END':
                        item_y = y + max_height - size.height()
                    if self.align_items == 'CENTER':
                        item_y = y + (max_height - size.height()) / 2
                    if self.align_items == 'STRETCH':
                        item_y = y
                        item_height = max_height

                    if self.item == 'GROW':
                        if count == 1:
                            item_width = size.width()
                        pass
                    else:
                        item_width = size.width()

                    # group_item.setGeometry(QtCore.QRect(QtCore.QPoint(item_x, item_y), QtCore.QSize(item_width, item_height)))
                    item_rect = QtCore.QRect(QtCore.QPoint(item_x, item_y), QtCore.QSize(item_width, item_height))
                    self.item_rects.append(item_rect)
                    item_x += item_width + item_spacing

                x = rect.x()
                y = y + max_height + spacing

                max_height = 0
                group_items = []
                group_width = 0

        rect.setBottom(y - spacing)
        rect = rect.marginsAdded(self.contents_margins)
        self.height = rect.height()

        self.viewport().update()

    def items(self):
        items = range(self.model().rowCount(self.rootIndex()))
        return items

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())

        self.update_item_rects()

        # rect = self.viewportRectForRow(0)
        # self.paintOutline(painter, rect)

        painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)

        # total_width = self.viewport().size().width()
        for row in range(self.model().rowCount(self.rootIndex())):
            index = self.model().index(row, 0, self.rootIndex())
            # rect = self.viewportRectForRow(row)
            # rect = QtCore.QRect(5, 5, 200, 200)
            # if (!rect.isValid() || rect.bottom() < 0 ||
            #     rect.y() > viewport().height()):
            #     continue

            option = QtWidgets.QStyleOptionViewItem(self.viewOptions())

            # size_hint = self.itemDelegate().sizeHint(option, index)
            # width = size_hint.width()
            # height = size_hint.height()
            width = 250
            height = 150

            # option.rect = QtCore.QRect(10, 10 + row * (height + 10), width, height)
            option.rect = self.item_rects[row]
            # logging.debug(option.rect)
            option.decorationAlignment = QtCore.Qt.AlignCenter
            option.decorationPosition = QtWidgets.QStyleOptionViewItem.Top
            option.displayAlignment = QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft

            if (self.selectionModel().isSelected(index)):
                option.state |= QtWidgets.QStyle.State_Selected
            if (self.currentIndex() == index):
                option.state |= QtWidgets.QStyle.State_HasFocus
            self.itemDelegate().paint(painter, option, index)

    def mousePressEvent(self, event):
        self.setCurrentIndex(self.indexAt(event.pos()))

        if not self.rubber_band:
            self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.rubber_origin = event.pos()
        self.rubber_band.setGeometry(QtCore.QRect(self.rubber_origin, QtCore.QSize()))
        self.rubber_band.show()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        rect = QtCore.QRect(self.rubber_origin, event.pos())
        self.rubber_band.setGeometry(rect.normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.rubber_band.hide()
        super().mouseReleaseEvent(event)

    # def edit(self, index, trigger, event):
    #     return super().edit(index, trigger, event)

    def indexWidget(self, index):
        # return self.model().itemFromIndex(index)
        return QtWidgets.QWidget()

    def indexAt(self, point):
        point += QtCore.QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())

        self.update_item_rects()

        for i, rect in enumerate(self.item_rects):
            if rect.contains(point):
                return self.model().index(i, 0, self.rootIndex())
        return QtCore.QModelIndex()

    def visualRegionForSelection(self, selection):
        region = QtGui.QRegion()

        for index in selection.indexes():
            row = index.row()
            region = region.united(self.item_rects[row])

        return region

    def setModel(self, model):
        self.item_rects = []
        super().setModel(model)

    def scrollContentsBy(self, dx, dy):
        self.scrollDirtyRegion(dx, dy)
        self.viewport().scroll(dx, dy)

    def horizontalOffset(self):
        return self.horizontalScrollBar().value()

    def verticalOffset(self):
        return self.verticalScrollBar().value()

    def setSelection(self, rect, flags):
        logging.debug(rect)

        rect = rect.translated(self.horizontalScrollBar().value(), self.verticalScrollBar().value()).normalized()
        self.update_item_rects()

        selection = QtCore.QItemSelection()
        for i, item_rect in enumerate(self.item_rects):
            if item_rect.intersects(rect):
                index = self.model().index(i, 0, self.rootIndex())
                selection.select(index, index)
        logging.debug(len(selection.indexes()))
        self.selectionModel().select(selection, flags)

    def visualRect(self, index):
        if index.isValid():
            return self.item_rects[index.row()]
        else:
            return QtCore.QRect()

    def moveCursor(self, cursor_action, modifiers):
        return QtCore.QModelIndex()

        index = self.currentIndex()
        if index.isValid():
            # if cursor_action == QtCore.Qt.MoveLeft and index.row() > 0 or
            return
    # QModelIndex index = currentIndex();
    # if (index.isValid()) {
    #     if ((cursorAction == MoveLeft && index.row() > 0) ||
    #         (cursorAction == MoveRight &&
    #          index.row() + 1 < model()->rowCount())) {
    #         const int offset = (cursorAction == MoveLeft ? -1 : 1);
    #         index = model()->index(index.row() + offset,
    #                                index.column(), index.parent());
    #     }
    #     else if ((cursorAction == MoveUp && index.row() > 0) ||
    #              (cursorAction == MoveDown &&
    #               index.row() + 1 < model()->rowCount())) {
    #         QFontMetrics fm(font());
    #         const int RowHeight = (fm.height() + ExtraHeight) *
    #                               (cursorAction == MoveUp ? -1 : 1);
    #         QRect rect = viewportRectForRow(index.row()).toRect();
    #         QPoint point(rect.center().x(),
    #                      rect.center().y() + RowHeight);
    #         while (point.x() >= 0) {
    #             index = indexAt(point);
    #             if (index.isValid())
    #                 break;
    #             point.rx() -= fm.width("n");
    #         }
    #     }
    # }
    # return index;

    def scrollTo(self, index, hint=QtWidgets.QAbstractItemView.EnsureVisible):
        return
    # QRect viewRect = viewport()->rect();
    # QRect itemRect = visualRect(index);

    # if (itemRect.left() < viewRect.left())
    #     horizontalScrollBar()->setValue(horizontalScrollBar()->value()
    #             + itemRect.left() - viewRect.left());
    # else if (itemRect.right() > viewRect.right())
    #     horizontalScrollBar()->setValue(horizontalScrollBar()->value()
    #             + qMin(itemRect.right() - viewRect.right(),
    #                    itemRect.left() - viewRect.left()));
    # if (itemRect.top() < viewRect.top())
    #     verticalScrollBar()->setValue(verticalScrollBar()->value() +
    #             itemRect.top() - viewRect.top());
    # else if (itemRect.bottom() > viewRect.bottom())
    #     verticalScrollBar()->setValue(verticalScrollBar()->value() +
    #             qMin(itemRect.bottom() - viewRect.bottom(),
    #                  itemRect.top() - viewRect.top()));
    # viewport()->update();

    # def startDrag(self, supported_actions):
    #     logging.debug(supported_actions)
    #     pass

    def rowsInserted(self, parent, start, end):
        self.item_rects = []
        super().rowsInserted(parent, start, end)

    def dataChanged(self, top_left, bottom_right, roles=None):
        if roles is None:
            roles = []
        self.item_rects = []
        super().dataChanged(top_left, bottom_right, roles)

    def rowsAboutToBeRemoved(self, parent, start, end):
        self.item_rects = []
        super().rowsAboutToBeRemoved(parent, start, end)

    def resizeEvent(self, event):
        self.item_rects = []
        # self.updateGeometries()

    # def updateGeometries(self):
    #     fm = self.font()
    #     row_height = fm.height() + ExtraHeight
    #     self.horizontalScrollBar().setSingleStep(fm.width("n"))
    #     self.horizontalScrollBar().setPageStep(self.viewport().width())
    #     self.horizontalScrollBar().setRange(0, max(0, idealWidth - self.viewport().width()))
    #     self.verticalScrollBar().setSingleStep(row_height)
    #     self.verticalScrollBar().setPageStep(self.viewport().height())
    #     self.verticalScrollBar().setRange(0, max(0, idealHeight - self.viewport().height()))
    #     return


def main():
    import qtdarkstyle

    logging.getLogger().setLevel(logging.DEBUG)

    app = QtWidgets.QApplication()
    qtdarkstyle.apply_style()

    path = r'D:\files\dev\027_flare\flare\flare\presets\lens'
    widget = FileBrowser(path)

    proxy = widget.proxy
    model = widget.model
    widget = FlexView()
    widget.setModel(model)

    f = app.font()
    f.setFamily('Fredoka One')
    # f.setPointSize(24)
    app.setFont(f)

    pixmap = QtGui.QPixmap(r'D:\files\dev\027_flare\flare\designer\starburst.png')
    pixmap = pixmap.scaledToWidth(200)
    for row in range(model.rowCount()):
        model.item(row, 0).setData(pixmap, QtCore.Qt.DecorationRole)

    widget.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
