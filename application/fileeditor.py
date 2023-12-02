from quof.utils import encdet
from quof.widgets import QBaseTextEdit, QBaseStatusBar

from PySide6.QtGui import QResizeEvent, QFont
from PySide6.QtWidgets import QWidget


class FileEditor(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)

        self._path = None
        self._encoding = "utf-8"

        self._editor = QBaseTextEdit(self)
        self._status = QBaseStatusBar(self)

        self._editor.setFont(QFont("Consolas"))
        self._editor.setWhitespaceEnabled(True)

    def path(self) -> str:
        return self._path

    def editor(self) -> QBaseTextEdit:
        return self._editor

    def loadFromFile(self, path: str) -> None:
        self._path = path
        with open(path, mode="rb") as file:
            text = file.read()

            self._encoding = encdet.detect(text)
            self._editor.setPlainText(
                text.decode(self._encoding)
            )

    def save(self) -> None:
        with open(self._path, mode="w", encoding=self._encoding) as file:
            file.write(
                encdet.convert(self._editor.toPlainText(), self._encoding)
            )

    def saveAs(self, path: str) -> None:
        self._path = path
        with open(self._path, mode="w", encoding=self._encoding) as file:
            file.write(
                encdet.convert(self._editor.toPlainText(), self._encoding)
            )

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._editor.resize(event.size().width(), event.size().height() - 30)

        self._status.resize(event.size().width(), 30)
        self._status.move(0, event.size().height() - 30)
