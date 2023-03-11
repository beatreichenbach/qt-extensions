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
        option_frame.palette.setColor(
            QtGui.QPalette.Window, palette.color(QtGui.QPalette.Dark)
        )
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
                pixmap, option.palette, option.state & QtWidgets.QStyle.State_Enabled
            )

        source_rect = QtWidgets.QStyle.alignedRect(
            option.direction, option.decorationAlignment, rect.size(), pixmap.rect()
        )

        painter.drawPixmap(rect, pixmap, source_rect)

    def drawDisplay(self, painter, option, rect, text):
        # get maximum
        rect.adjust(
            self.textMargins.left(),
            0,
            -self.textMargins.right(),
            -self.textMargins.bottom(),
        )
        super().drawDisplay(painter, option, rect, text)

    def sizeHint(self, option, index):
        size_hint = super().sizeHint(option, index)
        return size_hint


class FlexView(QtWidgets.QListView):
    class PositionFlags(Enum):
        START = auto()
        END = auto()
        CENTER = auto()
        STRETCH = auto()

        SPACE_BETWEEN = auto()
        # SPACE_AROUND = auto()
        # SPACE_EVENLY = auto()

    class ItemFlags(Enum):
        NO_GROW = auto()
        GROW = auto()
        MATCH_PREVIOUS = auto()

    class LayoutFlags(Enum):
        ROW = auto()
        ROW_REVERSE = auto()
        COLUMN = auto()
        COLUMN_REVERSE = auto()

    class WrapFlags(Enum):
        NONE = 0
        WRAP = auto()
        WRAP_REVERSE = auto()

    flex_direction: LayoutFlags = LayoutFlags.ROW
    align_content: PositionFlags = PositionFlags.START
    justify_content: PositionFlags = PositionFlags.START
    align_items: PositionFlags = PositionFlags.STRETCH
    wrap: WrapFlags = WrapFlags.WRAP
    item: ItemFlags = ItemFlags.NO_GROW

    min_size = QtCore.QSize()
    default_size = QtCore.QSize()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._item_rects = []
        self._pressed_position = QtCore.QPoint()
        self._rubber_rect = QtCore.QRect()

        self.contents_margins = QtCore.QMargins(6, 6, 6, 6)

        self.items = []
        self.height = 0

        # defaults
        self.setItemDelegate(FlexItemDelegate())
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionRectVisible(True)

    @property
    def item_rects(self) -> list[QtCore.QRect]:
        if not self._item_rects:
            self._item_rects = self._update_item_rects()
        return self._item_rects

    @item_rects.setter
    def item_rects(self, value: list[QtCore.QRect]) -> None:
        self._item_rects = value

    def dataChanged(
        self,
        top_left: QtCore.QModelIndex,
        bottom_right: QtCore.QModelIndex,
        roles: list[QtCore.Qt.ItemDataRole] | None = None,
    ) -> None:
        if roles is None:
            roles = []
        self.item_rects = []
        super().dataChanged(top_left, bottom_right, roles)

    def indexAt(self, point: QtCore.QPoint) -> QtCore.QModelIndex:
        point += QtCore.QPoint(
            self.horizontalScrollBar().value(), self.verticalScrollBar().value()
        )

        self.item_rects = []

        for i, rect in enumerate(self.item_rects):
            if rect.contains(point):
                return self.model().index(i, 0, self.rootIndex())
        return self.rootIndex()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self._pressed_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if not self.isVisible():
            return
        super().mouseMoveEvent(event)

        multi_selection_mode = self.selectionMode() not in (
            QtWidgets.QAbstractItemView.SingleSelection,
            QtWidgets.QAbstractItemView.NoSelection,
        )

        if (
            self.state() == QtWidgets.QAbstractItemView.DragSelectingState
            and self.isSelectionRectVisible()
            and multi_selection_mode
        ):
            offset = QtCore.QPoint(self.horizontalOffset(), self.verticalOffset())
            target_pos = event.pos() + offset
            rect = QtCore.QRect(self._pressed_position, target_pos)
            rect = rect.normalized()
            self.viewport().update(
                self._map_to_viewport(rect.united(self._rubber_rect))
            )
            self._rubber_rect = rect

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self.isSelectionRectVisible() and self._rubber_rect.isValid():
            self.viewport().update(self._map_to_viewport(self._rubber_rect))
            self._rubber_rect = QtCore.QRect()

    def moveCursor(
        self,
        cursor_action: QtWidgets.QAbstractItemView.CursorAction,
        modifiers: QtCore.Qt.KeyboardModifiers,
    ) -> QtCore.QModelIndex:
        match cursor_action:
            case QtWidgets.QAbstractItemView.MoveLeft:
                cursor_action = QtWidgets.QAbstractItemView.MoveUp
            case QtWidgets.QAbstractItemView.MoveRight:
                cursor_action = QtWidgets.QAbstractItemView.MoveDown
        return super().moveCursor(cursor_action, modifiers)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self.viewport())

        painter.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing
        )

        option = QtWidgets.QStyleOptionViewItem(self.viewOptions())
        state = option.state
        enabled = bool(state & QtWidgets.QStyle.State_Enabled)
        has_focus = self.hasFocus() or self.viewport().hasFocus()
        focused = has_focus and self.currentIndex().isValid()

        for row in range(self.model().rowCount(self.rootIndex())):
            index = self.model().index(row, 0, self.rootIndex())

            option.state = state
            option.rect = self.item_rects[row]
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

        if self.isSelectionRectVisible() and self._rubber_rect.isValid():
            option_rubber = QtWidgets.QStyleOptionRubberBand()
            option_rubber.initFrom(self)
            option_rubber.shape = QtWidgets.QRubberBand.Rectangle
            option_rubber.opaque = False
            rect = self._map_to_viewport(self._rubber_rect, False)
            viewport_rect = self.viewport().rect().adjusted(-16, -16, 16, 16)
            option_rubber.rect = rect.intersected(viewport_rect)
            painter.save()
            self.style().drawControl(
                QtWidgets.QStyle.CE_RubberBand, option_rubber, painter
            )
            painter.restore()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.item_rects = []
        super().resizeEvent(event)

    def rowsAboutToBeRemoved(
        self, parent: QtCore.QModelIndex, start: int, end: int
    ) -> None:
        self.item_rects = []
        super().rowsAboutToBeRemoved(parent, start, end)

    def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int) -> None:
        self.item_rects = []
        super().rowsInserted(parent, start, end)

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.item_rects = []
        super().setModel(model)

    # def setSelection(
    #     self, rect: QtCore.QRect, command: QtCore.QItemSelectionModel.SelectionFlags
    # ) -> None:
    #     rect = rect.translated(
    #         self.horizontalScrollBar().value(), self.verticalScrollBar().value()
    #     ).normalized()
    #     self.update_item_rects()
    #
    #     selection = QtCore.QItemSelection()
    #     for i, item_rect in enumerate(self.item_rects):
    #         if item_rect.intersects(rect):
    #             index = self.model().index(i, 0, self.rootIndex())
    #             selection.select(index, index)
    #     self.selectionModel().select(selection, command)

    def visualRect(self, index: QtCore.QModelIndex) -> QtCore.QRect:
        if index.isValid():
            rect = self.item_rects[index.row()]
        else:
            rect = QtCore.QRect()
        return rect

    def visualRegionForSelection(
        self, selection: QtCore.QItemSelection
    ) -> QtGui.QRegion:
        region = QtGui.QRegion()

        for index in selection.indexes():
            row = index.row()
            region = region.united(self.item_rects[row])

        return region

    def _map_to_viewport(
        self, rect: QtCore.QRect, extend: bool = False
    ) -> QtCore.QRect:
        if not rect.isValid():
            return rect
        result = QtCore.QRect(rect)
        if extend:
            result.setLeft(self.spacing())
            result.setWidth(
                max(
                    rect.width(),
                    max(self.contentsSize().width(), self.viewport().width())
                    - 2 * self.spacing(),
                )
            )

        dx = -self.horizontalOffset()
        dy = -self.verticalOffset()
        rect = result.adjusted(dx, dy, dx, dy)
        return rect

    def _update_item_rects(self) -> list[QtCore.QRect]:
        ItemFlags = self.__class__.ItemFlags
        PositionFlags = self.__class__.PositionFlags

        default_size = QtCore.QSize(250, 150)
        rect = self.viewport().rect()
        rect = rect.marginsRemoved(self.contents_margins)
        x = rect.x()
        y = rect.y()
        max_height = 0
        group_width = 0
        spacing = self.spacing()
        item_rects = []

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

            is_last_item = i == len(items) - 1
            is_overlapped = next_next_x > rect.right()

            if self.wrap:
                end_group = is_overlapped or is_last_item
            else:
                end_group = is_last_item

            if end_group:
                count = len(group_items)
                item_spacing = spacing
                group_width -= spacing

                if (
                    self.item == ItemFlags.GROW
                    or self.justify_content == PositionFlags.START
                ):
                    item_x = rect.x()
                elif self.justify_content == PositionFlags.END:
                    item_x = rect.right() - group_width
                elif self.justify_content == PositionFlags.CENTER:
                    total_space = rect.width() - group_width
                    item_x = rect.x() + total_space / 2
                elif self.justify_content == PositionFlags.SPACE_BETWEEN:
                    total_space = rect.width() - group_width + (count - 1) * spacing
                    item_x = rect.x()
                    item_spacing = total_space / max(1, count - 1)

                item_width = (rect.width() - (count - 1) * spacing) / count

                for j, group_item in enumerate(group_items):
                    # size = group_item.sizeHint()
                    size = default_size
                    item_height = size.height()

                    if self.align_items == PositionFlags.START:
                        item_y = y
                    if self.align_items == PositionFlags.END:
                        item_y = y + max_height - size.height()
                    if self.align_items == PositionFlags.CENTER:
                        item_y = y + (max_height - size.height()) / 2
                    if self.align_items == PositionFlags.STRETCH:
                        item_y = y
                        item_height = max_height

                    if self.item == ItemFlags.GROW:
                        if count == 1:
                            item_width = size.width()
                        pass
                    else:
                        item_width = size.width()

                    # group_item.setGeometry(QtCore.QRect(QtCore.QPoint(item_x, item_y), QtCore.QSize(item_width, item_height)))
                    item_rect = QtCore.QRect(
                        QtCore.QPoint(item_x, item_y),
                        QtCore.QSize(item_width, item_height),
                    )
                    item_rects.append(item_rect)
                    item_x += item_width + item_spacing

                x = rect.x()
                y = y + max_height + spacing

                max_height = 0
                group_items = []
                group_width = 0

        rect.setBottom(y - spacing)
        rect = rect.marginsAdded(self.contents_margins)
        self.height = rect.height()

        # self.viewport().update()
        return item_rects
