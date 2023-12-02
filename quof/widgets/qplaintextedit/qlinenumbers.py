from PySide6.QtCore import QSize
from PySide6.QtGui import QPaintEvent, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QWidget


class QLineNumberArea(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._editor = parent

        self._start_select = False
        self._select_start = -1
        self._select_end = -1

    @property
    def sizeHint(self) -> QSize:
        return QSize(self._editor.lineNumberAreaWidth(), 0)  # noqa

    def paintEvent(self, event: QPaintEvent) -> None:
        self._editor.lineNumberAreaPaintEvent(event)  # noqa

    def wheelEvent(self, event: QWheelEvent) -> None:
        self._editor.verticalScrollBar().setValue(  # noqa
            self._editor.verticalScrollBar().value() - (event.angleDelta().y() // abs(event.angleDelta().y()))  # noqa
        )

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._editor.selectLines(-1, -1)  # noqa

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._start_select = True
        self._select_start = self._select_end = self._editor.lineFromPosition(int(event.position().y()))  # noqa

        self._editor.selectLines(self._select_start, self._select_end)  # noqa

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._start_select:
            self._select_end = self._editor.lineFromPosition(int(event.position().y()))  # noqa
            if self._select_end != -1:
                self._editor.selectLines(self._select_start, self._select_end)  # noqa

            """
            if event.position().y() <= 10:
                self._editor.verticalScrollBar().setValue(self._editor.verticalScrollBar().value() - 1)  # noqa
            elif event.position().y() >= self.height() - 10:
                self._editor.verticalScrollBar().setValue(self._editor.verticalScrollBar().value() + 1)  # noqa
            """  # Auto scroll test ( The result is not the best )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._start_select = False
        self._select_start = -1
        self._select_end = -1
