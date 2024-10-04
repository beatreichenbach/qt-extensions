from __future__ import annotations

from collections.abc import Sequence

from enum import auto, Enum

from PySide2 import QtWidgets, QtCore, QtGui

ScrollHint = QtWidgets.QAbstractItemView.ScrollHint


class FlexItemDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.text_margins = QtCore.QMargins(4, 4, 4, 4)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        # draw frame
        self._draw_frame(painter, option)

        # draw decoration and display
        option_view_item = QtWidgets.QStyleOptionViewItem(option)
        # option_view_item.state &= ~QtWidgets.QStyle.State_Selected

        super().paint(painter, option_view_item, index)

        # draw selection
        # self._draw_selection(painter, option)

        # draw focus
        super().drawFocus(painter, option, option.rect)

    def drawFocus(self, painter, option, rect) -> None:
        return

    def drawDecoration(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        rect: QtCore.QRect,
        pixmap: QtGui.QPixmap,
    ) -> None:
        option.rect.adjust(2, 2, -2, -2)
        # margins = self.text_margins
        # option.rect.adjust(margins.left(), margins.top(), -margins.right(), 0)

        font_metrics = painter.fontMetrics()
        height = font_metrics.height()
        height += self.text_margins.top() + self.text_margins.bottom()

        rect = QtCore.QRect(option.rect)
        rect.setHeight(option.rect.height() - height)

        if pixmap is None or not rect.isValid():
            return

        pixmap = pixmap.scaled(rect.size(), QtCore.Qt.KeepAspectRatioByExpanding)

        # if hasattr(painter, 'selected') and painter.selected:
        if option.state & QtWidgets.QStyle.State_Selected:
            pixmap = self.selectedPixmap(
                pixmap, option.palette, option.state & QtWidgets.QStyle.State_Enabled
            )

        source_rect = QtWidgets.QStyle.alignedRect(
            option.direction, option.decorationAlignment, rect.size(), pixmap.rect()
        )

        painter.drawPixmap(rect, pixmap, source_rect)

    def drawDisplay(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        rect: QtCore.QRect,
        text: str,
    ) -> None:
        rect.adjust(
            self.text_margins.left(),
            0,
            -self.text_margins.right(),
            -self.text_margins.bottom(),
        )
        option.state &= ~QtWidgets.QStyle.State_Selected
        super().drawDisplay(painter, option, rect, text)

    def sizeHint(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> QtCore.QSize:
        size_hint = super().sizeHint(option, index)
        # size_hint = option.rect.size()
        return size_hint

        # value = index.data(QtCore.Qt.SizeHintRole)
        # if value.isValid():
        #     return value
        #
        # decorationRect = self.rect(option, index, QtCore.Qt.DecorationRole)
        # checkRect = self.rect(option, index, QtCore.Qt.CheckStateRole)
        # displayRect = self.displayRect(index, option, decorationRect, checkRect)
        #
        # # doLayout(option, &checkRect, &decorationRect, &displayRect, True)
        # return (decorationRect | displayRect | checkRect).size()

    @staticmethod
    def _draw_frame(
        painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem
    ) -> None:
        widget = option.widget
        style = widget.style() or QtWidgets.QApplication.style()
        option_frame = QtWidgets.QStyleOptionFrame()

        palette = option_frame.palette
        option_frame.palette.setColor(
            QtGui.QPalette.Window, palette.color(QtGui.QPalette.Dark)
        )
        option_frame.state = option.state
        option_frame.rect = option.rect
        option_frame.rect.adjust(1, 1, -1, -1)
        option_frame.frameShape = QtWidgets.QFrame.StyledPanel
        option_frame.lineWidth = 1

        if option.state & QtWidgets.QStyle.State_Selected:
            color = palette.color(QtGui.QPalette.Highlight)
        else:
            color = palette.color(QtGui.QPalette.Window)
        painter.fillRect(option_frame.rect, color)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        style.drawPrimitive(QtWidgets.QStyle.PE_Frame, option_frame, painter)
        # painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.restore()

    @staticmethod
    def _draw_selection(
        painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem
    ) -> None:
        if option.state & QtWidgets.QStyle.State_Selected:
            palette = option.palette
            color = palette.color(QtGui.QPalette.Highlight)
            pen = QtGui.QPen(color)
            painter.save()
            painter.setPen(pen)
            painter.drawRect(option.rect)
            painter.restore()


class FlexView(QtWidgets.QAbstractItemView):
    class PositionFlags(Enum):
        START = auto()
        END = auto()
        CENTER = auto()
        STRETCH = auto()

        SPACE_BETWEEN = auto()
        # SPACE_AROUND = auto()
        # SPACE_EVENLY = auto()

    class LayoutFlags(Enum):
        ROW = auto()
        # ROW_REVERSE = auto()
        # COLUMN = auto()
        # COLUMN_REVERSE = auto()

    class WrapFlags(Enum):
        NONE = 0
        WRAP = auto()
        # WRAP_REVERSE = auto()

    flex_direction: LayoutFlags = LayoutFlags.ROW
    align_content: PositionFlags = PositionFlags.START
    justify_content: PositionFlags = PositionFlags.START
    align_items: PositionFlags = PositionFlags.STRETCH
    wrap: WrapFlags = WrapFlags.WRAP
    grow: bool = False

    min_size = QtCore.QSize(0, 0)
    default_size = QtCore.QSize(250, 150)
    child_rows = True
    column = 0

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._item_rects = []
        self._rubber_origin = QtCore.QPoint()
        self._rubber_band = None

        self.height = 0
        self.min_item_width = 0

        self.contents_margins = QtCore.QMargins(6, 6, 6, 6)
        self.spacing = 4

        # defaults
        self.setItemDelegate(FlexItemDelegate())
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    @property
    def item_rects(self) -> dict[QtCore.QModelIndex, QtCore.QRect]:
        if not self._item_rects:
            self._item_rects = self._update_item_rects()
        return self._item_rects

    @item_rects.setter
    def item_rects(self, value: dict[QtCore.QModelIndex, QtCore.QRect]) -> None:
        self._item_rects = value

    def dataChanged(
        self,
        top_left: QtCore.QModelIndex,
        bottom_right: QtCore.QModelIndex,
        roles: Sequence[QtCore.Qt.ItemDataRole] | None = None,
    ) -> None:
        if roles is None:
            roles = []
        self.item_rects = {}
        super().dataChanged(top_left, bottom_right, roles)

    def indexAt(self, point: QtCore.QPoint) -> QtCore.QModelIndex:
        offset = QtCore.QPoint(
            self.horizontalScrollBar().value(), self.verticalScrollBar().value()
        )
        point += offset

        self.item_rects = {}

        for index, rect in self.item_rects.items():
            if rect.contains(point):
                return index
        return self.rootIndex()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)

        self.indexAt(event.pos())

        # rubber_band
        if event.button() == QtCore.Qt.LeftButton:
            if not self._rubber_band:
                self._rubber_band = QtWidgets.QRubberBand(
                    QtWidgets.QRubberBand.Rectangle, self
                )
            self._rubber_origin = event.pos()
            rect = QtCore.QRect(self._rubber_origin, QtCore.QSize())
            self._rubber_band.setGeometry(rect)
            self._rubber_band.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        if isinstance(self._rubber_band, QtWidgets.QWidget):
            rect = QtCore.QRect(self._rubber_origin, event.pos())
            self._rubber_band.setGeometry(rect.normalized())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if isinstance(self._rubber_band, QtWidgets.QWidget):
            self._rubber_band.hide()

    def moveCursor(
        self,
        cursor_action: QtWidgets.QAbstractItemView.CursorAction,
        modifiers: QtCore.Qt.KeyboardModifiers,
    ) -> QtCore.QModelIndex:
        view = QtWidgets.QAbstractItemView
        index = self.currentIndex()
        if index.isValid():
            row = index.row()

            min_row = 0
            max_row = self.model().rowCount(index.parent()) - 1

            if cursor_action in (view.MoveLeft | view.MoveUp | view.MovePrevious):
                row -= 1
            elif cursor_action in (view.MoveRight | view.MoveDown | view.MoveNext):
                row += 1
            elif cursor_action == view.MoveHome:
                row = min_row
            elif cursor_action == view.MoveEnd:
                row = max_row
            elif cursor_action == view.MovePageUp:
                row -= 10
            elif cursor_action == view.MovePageDown:
                row += 10
            else:
                return index

            row = max(min_row, min(max_row, row))

            index = self.model().index(row, index.column(), index.parent())
        return index

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self.viewport())

        painter.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing
        )

        option = QtWidgets.QStyleOptionViewItem(self.viewOptions())
        state = option.state
        enabled = bool(state & QtWidgets.QStyle.State_Enabled)
        has_focus = self.hasFocus() or self.viewport().hasFocus()
        focused = has_focus and self.currentIndex().isValid()

        for index in self._indexes():
            rect = self.item_rects.get(index)
            if rect is None:
                continue
            option.state = state
            option.rect = self._map_to_viewport(rect)
            option.decorationAlignment = QtCore.Qt.AlignCenter
            option.decorationPosition = QtWidgets.QStyleOptionViewItem.Top
            option.displayAlignment = QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft

            if self.selectionModel().isSelected(index):
                option.state |= QtWidgets.QStyle.State_Selected
            if enabled:
                if self.model().flags(index) & QtCore.Qt.ItemIsEnabled:
                    current_color_group = QtGui.QPalette.Normal
                else:
                    option.state &= ~QtWidgets.QStyle.State_Enabled
                    current_color_group = QtGui.QPalette.Disabled
                option.palette.setCurrentColorGroup(current_color_group)
            if focused and self.currentIndex() == index:
                option.state |= QtWidgets.QStyle.State_HasFocus
                if self.state() == QtWidgets.QAbstractItemView.EditingState:
                    option.state |= QtWidgets.QStyle.State_Editing
            self.itemDelegate(index).paint(painter, option, index)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.item_rects = {}
        super().resizeEvent(event)

    def rowsAboutToBeRemoved(
        self, parent: QtCore.QModelIndex, start: int, end: int
    ) -> None:
        self.item_rects = {}
        super().rowsAboutToBeRemoved(parent, start, end)

    def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int) -> None:
        self.item_rects = {}
        super().rowsInserted(parent, start, end)

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.item_rects = {}
        super().setModel(model)

    def scrollTo(
        self,
        index: QtCore.QModelIndex,
        hint: ScrollHint = QtWidgets.QAbstractItemView.EnsureVisible,
    ) -> None:
        if index.parent() != self.rootIndex():
            return

        if not index.isValid():
            return

        rect = self.item_rects[index]
        mapped_rect = self._map_to_viewport(rect)

        if (
            hint == QtWidgets.QAbstractItemView.EnsureVisible
            and self.viewport().rect().contains(mapped_rect)
        ):
            self.viewport().update(mapped_rect)
            return

        horizontal_value = self._horizontal_scroll_to_value(rect, hint)
        self.horizontalScrollBar().setValue(horizontal_value)
        vertical_value = self._vertical_scroll_to_value(rect, hint)
        self.verticalScrollBar().setValue(vertical_value)

    def horizontalOffset(self) -> int:
        return self.horizontalScrollBar().value()

    def verticalOffset(self) -> int:
        return self.verticalScrollBar().value()

    def selectionChanged(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        super().selectionChanged(selected, deselected)
        self.viewport().update()

    def setSelection(
        self, rect: QtCore.QRect, command: QtCore.QItemSelectionModel.SelectionFlags
    ) -> None:
        rect = rect.translated(self.horizontalOffset(), self.verticalOffset())
        rect = rect.normalized()

        update_rect = QtCore.QRect()
        selection = QtCore.QItemSelection()
        for index, item_rect in self.item_rects.items():
            if item_rect.intersects(rect):
                update_rect = update_rect.united(item_rect)
                selection.select(index, index)
        self.selectionModel().select(selection, command)

    def update(self) -> None:
        super().update()
        self.viewport().update()

    def updateGeometries(self) -> None:
        self._update_scrollbars()
        super().updateGeometries()

    def visualRect(self, index: QtCore.QModelIndex) -> QtCore.QRect:
        if index.isValid():
            rect = self.item_rects[index]
        else:
            rect = QtCore.QRect()
        return self._map_to_viewport(rect)

    def visualRegionForSelection(
        self, selection: QtCore.QItemSelection
    ) -> QtGui.QRegion:
        region = QtGui.QRegion()

        for index in selection.indexes():
            rect = self.item_rects[index]
            region = region.united(self._map_to_viewport(rect))

        return region

    def _indexes(
        self, parent: QtCore.QModelIndex | None = None
    ) -> tuple[QtCore.QModelIndex, ...]:
        if parent is None:
            parent = self.rootIndex()
        indexes = []
        for row in range(self.model().rowCount(parent)):
            index = self.model().index(row, self.column, parent)
            if index.data():  # TODO: temporary
                indexes.append(index)
            if self.child_rows:
                first_index = index.siblingAtColumn(0)
                if first_index.isValid():
                    indexes.extend(self._indexes(first_index))
        return tuple(indexes)

    def _horizontal_scroll_to_value(
        self, rect: QtCore.QRect, hint: ScrollHint
    ) -> float:
        if hint == QtWidgets.QAbstractItemView.PositionAtBottom:
            value = rect.right() - self.viewport().width() + self.spacing
        elif hint == QtWidgets.QAbstractItemView.PositionAtCenter:
            value = rect.left() + rect.width() / 2 - (self.viewport().width() / 2)
        else:
            value = rect.left() - self.spacing
        return value

    def _vertical_scroll_to_value(self, rect: QtCore.QRect, hint: ScrollHint) -> float:
        if hint == QtWidgets.QAbstractItemView.PositionAtBottom:
            value = rect.bottom() - self.viewport().height() + self.spacing
        elif hint == QtWidgets.QAbstractItemView.PositionAtCenter:
            value = rect.top() + rect.height() / 2 - (self.viewport().height() / 2)
        else:
            value = rect.top() - self.spacing
        return value

    def _map_to_viewport(
        self, rect: QtCore.QRect, extend: bool = False
    ) -> QtCore.QRect:
        if not rect.isValid():
            return rect
        result = QtCore.QRect(rect)
        if extend:
            result.setLeft(self.spacing)
            result.setWidth(
                max(
                    rect.width(),
                    max(self.contentsSize().width(), self.viewport().width())
                    - 2 * self.spacing,
                )
            )

        dx = -self.horizontalOffset()
        dy = -self.verticalOffset()
        rect = result.adjusted(dx, dy, dx, dy)
        return rect

    def _update_item_rects(self) -> dict[QtCore.QModelIndex, QtCore.QRect]:
        if not self.model():
            return {}

        position_flags = self.__class__.PositionFlags
        wrap_flags = self.__class__.WrapFlags

        default_size = self.default_size
        rect = self.viewport().rect()
        rect = rect.marginsRemoved(self.contents_margins)
        x = rect.x()
        y = rect.y()
        max_height = 0
        group_width = 0
        spacing = self.spacing
        item_rects = {}
        min_item_width = 0
        previous_item_width = default_size.width()

        indexes = self._indexes()
        group_indexes = []
        for i, index in enumerate(indexes):
            group_indexes.append(index)
            max_height = max(max_height, default_size.height())
            next_x = x + default_size.width() + spacing
            group_width += default_size.width() + spacing
            x = next_x

            try:
                # next_next_x = next_x + items[i + 1].sizeHint().width()
                next_next_x = next_x + default_size.width()
            except IndexError:
                next_next_x = next_x - spacing

            is_last_item = i == len(indexes) - 1
            is_overlapped = next_next_x > rect.right()

            if self.wrap == wrap_flags.WRAP:
                end_group = is_overlapped or is_last_item
            else:
                end_group = True

            if end_group:
                count = len(group_indexes)
                item_spacing = spacing
                group_width -= spacing

                # x position
                if self.justify_content == position_flags.START or self.grow:
                    item_x = rect.x()
                elif self.justify_content == position_flags.END:
                    item_x = rect.right() - group_width
                elif self.justify_content == position_flags.CENTER:
                    total_space = rect.width() - group_width
                    item_x = rect.x() + total_space / 2
                elif self.justify_content == position_flags.SPACE_BETWEEN:
                    total_space = rect.width() - group_width + (count - 1) * spacing
                    item_x = rect.x()
                    item_spacing = total_space / max(1, count - 1)
                else:
                    item_x = rect.x()

                item_width = (rect.width() - (count - 1) * spacing) / count
                for group_index in group_indexes:
                    # size = group_item.sizeHint()
                    size = default_size
                    item_height = size.height()

                    # y position
                    if self.align_items == position_flags.START:
                        item_y = y
                    elif self.align_items == position_flags.END:
                        item_y = y + max_height - size.height()
                    elif self.align_items == position_flags.CENTER:
                        item_y = y + (max_height - size.height()) / 2
                    elif self.align_items == position_flags.STRETCH:
                        item_y = y
                        item_height = max_height
                    else:
                        item_y = y

                    # size
                    if self.grow:
                        if is_last_item:
                            item_width = previous_item_width
                        else:
                            previous_item_width = item_width
                    else:
                        item_width = size.width()

                    item_rect = QtCore.QRect(
                        QtCore.QPoint(item_x, item_y),
                        QtCore.QSize(item_width, item_height),
                    )

                    min_item_width = max(item_rect.width(), min_item_width)
                    item_rects[group_index] = item_rect
                    item_x += item_width + item_spacing

                x = rect.x()
                y = y + max_height + spacing

                max_height = 0
                group_indexes = []
                group_width = 0

        rect.setBottom(y - spacing)
        rect = rect.marginsAdded(self.contents_margins)
        self.height = rect.height()
        self.min_item_width = (
            min_item_width
            + self.contents_margins.left()
            + self.contents_margins.right()
        )

        return item_rects

    def _update_scrollbars(self) -> None:
        self._update_item_rects()

        viewport = self.viewport()

        self.verticalScrollBar().setPageStep(viewport.height())
        self.verticalScrollBar().setRange(0, self.height - viewport.height())

        self.horizontalScrollBar().setPageStep(viewport.width())
        self.horizontalScrollBar().setRange(0, self.min_item_width - viewport.width())
