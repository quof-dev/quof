from PySide6.QtWidgets import QWidget, QMenuBar


class QBaseMenuBar(QMenuBar):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
