from quof.core.qlocale import QText

from PySide6.QtWidgets import QTabWidget, QWidget


class QBaseTabWidget(QTabWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

    def addTab(self, title: QText | str, widget: QWidget) -> int:
        if isinstance(title, QText):
            title.textChanged.connect(
                lambda: self.setTabText(self.indexOf(widget), title.text())
            )

        index = super().addTab(
            widget, title.text() if isinstance(title, QText) else title
        )
        self.setCurrentIndex(index)

        return index
