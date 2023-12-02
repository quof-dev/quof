import sys

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPaintEvent
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QApplication


class MiniMapWidget(QWidget):
    def __init__(self, parent: QPlainTextEdit):
        super().__init__(parent)

        self._text_edit = parent
        self._font_metrics = QFontMetrics(self._text_edit.font())
        # self._syntax_highlighter = self._text_edit.syntax_highlighter()

        self._update_mini_map()

    def sizeHint(self) -> QSize:
        return QSize(self._text_edit.width(), self._text_edit.height() // 16)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.fillRect(event.rect(), Qt.GlobalColor.lightGray)

        for line in range(self._text_edit.blockCount()):
            line = self._text_edit.document().findBlockByLineNumber(line)
            top = self._text_edit.blockBoundingGeometry(line).translated(self._text_edit.contentOffset()).top()
            bottom = top + self._text_edit.blockBoundingRect(line).height()

            painter.setPen(QColor(0, 0, 0, 128))
            painter.drawLine(0, int(top), self.width(), int(top))

            # painter.setPen(self._syntax_highlighter.color(line))
            painter.drawRect(0, int(top), self.width(), int(bottom - top))

    def _update_mini_map(self) -> None:
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    text_edit = QPlainTextEdit()
    text_edit.setPlainText("This is a test.")

    mini_map = MiniMapWidget(text_edit)

    text_edit.show()
    mini_map.show()

    sys.exit(app.exec())
