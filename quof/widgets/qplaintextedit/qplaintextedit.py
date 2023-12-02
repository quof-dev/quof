from .qlinenumbers import QLineNumberArea

from quof.gui.qstyle import QStyle
from quof.gui.qsyntaxhighlighter import QBaseSyntaxHighlighter

from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtGui import (QColor, QTextFormat, QPainter, QPaintEvent, QResizeEvent,
                           QTextCursor, QTextCharFormat, QTextDocument, QWheelEvent, QFont, QTextOption)
from PySide6.QtWidgets import QWidget, QPlainTextEdit, QTextEdit, QApplication


class QBaseTextEdit(QPlainTextEdit):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)

        self._line_number_area = QLineNumberArea(self)
        self._syntax_highlighter = QBaseSyntaxHighlighter(self.document())

        self._visible_blocks = []
        self._zoom_enable = True

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)  # noqa
        self.updateRequest.connect(self.updateLineNumberArea)  # noqa
        self.cursorPositionChanged.connect(self.highlightCurrentLine)  # noqa

        self.horizontalScrollBar().setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.verticalScrollBar().setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        self.document().setDocumentMargin(0)
        self.ensureCursorVisible()

        QStyle.markAsCustom("QBaseTextEdit->line-numbers-area-background")
        QStyle.markAsCustom("QBaseTextEdit->line-numbers-background")
        QStyle.markAsCustom("QBaseTextEdit->line-numbers-color")
        QStyle.markAsCustom("QBaseTextEdit->current-line-background")

    def isUndoAvailable(self) -> bool:
        return self.document().isUndoAvailable()

    def isRedoAvailable(self) -> bool:
        return self.document().isRedoAvailable()

    def hasSelectedText(self) -> bool:
        return not not self.textCursor().selectedText()

    def hasPlainText(self) -> bool:
        return not not self.toPlainText()

    @staticmethod
    def hasTextToPaste() -> bool:
        return not not QApplication.clipboard().text()

    def zoom(self, delta: int) -> None:
        if delta > 0:
            self.zoomIn(abs(delta))
        else:
            self.zoomOut(abs(delta))

        self.updateLineNumberAreaFont()
        self.updateLineNumberAreaWidth(0)

    def setFont(self, font: QFont) -> None:
        self._line_number_area.setFont(font)

        super().setFont(font)

    def setSyntaxHighlighter(self, highlighter: type[QBaseSyntaxHighlighter]) -> None:
        self._syntax_highlighter = highlighter(self.document())

    def setWordWrapEnabled(self, state: bool) -> None:
        if state:
            self.setWordWrapMode(
                QTextOption.WrapMode.WordWrap
            )
        else:
            self.setWordWrapMode(
                QTextOption.WrapMode.NoWrap
            )

    def lineFromPosition(self, pos: int) -> int:
        height = self.fontMetrics().height()
        for top, line, block in self._visible_blocks:
            if top <= pos <= top + height:
                return line
        return -1

    def selectLines(self, start: int = 0, end: int = 0) -> None:
        if end == -1:
            end = self.document().blockCount() - 1
        if start < 0:
            start = 0

        cursor = self.textCursor()
        cursor.setPosition(
            self.document().findBlockByNumber(start).position()
        )

        if end > start:
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor, end - start)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        elif end < start:
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.MoveAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.KeepAnchor, start - end)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        self.setTextCursor(cursor)

    def setWhitespaceEnabled(self, state: bool) -> None:
        options = self.document().defaultTextOption()

        if state:
            options.setFlags(options.flags() | QTextOption.Flag.ShowTabsAndSpaces)
        else:
            options.setFlags(options.flags() & ~QTextOption.Flag.ShowTabsAndSpaces)

        options.setFlags(
            options.flags() | QTextOption.Flag.AddSpaceForLineAndParagraphSeparators
        )

        self.document().setDefaultTextOption(options)

    def updateVisibleBlocks(self) -> None:
        self._visible_blocks = []

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid():
            if bottom > self.height():
                break
            if block.isVisible():
                self._visible_blocks.append((top, block_number, block))

            block = block.next()

            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

            block_number += 1

    def updateEndScroll(self) -> None:
        frame_format = self.document().rootFrame().frameFormat()
        frame_format.setBottomMargin(25)

        self.document().rootFrame().setFrameFormat(frame_format)

    def highlightFound(self, pattern: str) -> None:
        document = self.document()

        highlight_cursor = QTextCursor(document)

        cursor = QTextCursor(document)
        cursor.beginEditBlock()

        color_format = QTextCharFormat(highlight_cursor.charFormat())
        color_format.setBackground(Qt.GlobalColor.yellow)

        while not highlight_cursor.isNull() and not highlight_cursor.atEnd():
            highlight_cursor = document.find(pattern, highlight_cursor, QTextDocument.FindFlag.FindWholeWords)

            if not highlight_cursor.isNull():
                highlight_cursor.movePosition(
                    QTextCursor.MoveOperation.WordRight,
                    QTextCursor.MoveMode.KeepAnchor
                )
                highlight_cursor.mergeCharFormat(color_format)

        cursor.endEditBlock()

    def clearCharFormat(self) -> None:
        cursor = self.textCursor()

        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()

        self.setTextCursor(cursor)

    def lineNumberAreaWidth(self) -> int:
        return int(self.font().pointSize()) + self.fontMetrics().horizontalAdvance("9") * len(f"{self.blockCount()}")

    def lineNumberAreaPaintEvent(self, event: QPaintEvent) -> None:
        area_background = QStyle.get(
            "QBaseTextEdit->line-numbers-area-background", default=Qt.GlobalColor.lightGray
        )
        rect_background = QStyle.get(
            "QBaseTextEdit->line-numbers-background", default=Qt.GlobalColor.darkGray
        )
        number_color = QStyle.get(
            "QBaseTextEdit->line-numbers-color", default=Qt.GlobalColor.black
        )

        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), area_background)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = self.blockBoundingRect(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and event.rect().bottom() >= top:
            if block.isVisible() and event.rect().top() <= bottom:
                if block_number == self.textCursor().blockNumber():
                    painter.fillRect(
                        QRect(-1, int(top), self._line_number_area.width() + 1, self.fontMetrics().height()),
                        QColor(rect_background).lighter(145)
                    )

                painter.setPen(number_color)
                painter.drawText(
                    0, int(top), self._line_number_area.width(), self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, f"{block_number + 1} "
                )

            block = block.next()

            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

            block_number += 1

    def updateLineNumberAreaFont(self) -> None:
        font = self._line_number_area.font()
        font.setPointSize(self.font().pointSize())

        self._line_number_area.setFont(font)

    @Slot(int)
    def updateLineNumberAreaWidth(self, _) -> None:
        self.setStyleSheet(f"QScrollBar:horizontal {{ margin-left: {self.lineNumberAreaWidth() + 15} }}")
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    @Slot()
    def highlightCurrentLine(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            background = QStyle.get(
                "QBaseTextEdit->current-line-background", default=Qt.GlobalColor.darkGray
            )

            selection.format.setBackground(QColor(background).lighter(145))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    @Slot(QRect, int)
    def updateLineNumberArea(self, rect: QRect, scroll: int) -> None:
        if scroll:
            self._line_number_area.scroll(0, scroll)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def paintEvent(self, event: QPaintEvent) -> None:
        self.updateVisibleBlocks()

        super().paintEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        rect = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(rect.left(), rect.top(), self.lineNumberAreaWidth(), rect.height())
        )

        super().resizeEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and self._zoom_enable:
            if event.angleDelta().y() < 0 and self.font().pointSize() > 6:
                self.zoomOut(1)
            elif event.angleDelta().y() > 0 and self.font().pointSize() < 60:
                self.zoomIn(1)
        else:
            super(QBaseTextEdit, self).wheelEvent(event)

        self.updateLineNumberAreaFont()
        self.updateLineNumberAreaWidth(0)
