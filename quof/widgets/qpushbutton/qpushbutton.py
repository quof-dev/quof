from quof.core.qlocale import QText

from PySide6.QtWidgets import QPushButton, QWidget


class QBasePushButton(QPushButton):
    def __init__(self, text: QText | str, parent: QWidget = None) -> None:
        super().__init__(text.text() if isinstance(text, QText) else text, parent)

        if isinstance(text, QText):
            text.textChanged.connect(
                lambda: self.setText(text.text())
            )

    def setTranslatableText(self, text: QText | str) -> None:
        self.setText(text.text() if isinstance(text, QText) else text)

        if isinstance(text, QText):
            text.textChanged.connect(
                lambda: self.setText(text.text())
            )
