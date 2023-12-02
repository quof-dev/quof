import sys

from PySide6.QtGui import QPixmap, QColor, QPainter


class QBasePixmap(QPixmap):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)

    def setColor(self, color: QColor) -> None:
        painter = QPainter(self)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(self.rect(), color)
        painter.end()
