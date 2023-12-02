from PySide6.QtWidgets import QFrame, QWidget


class QBaseStatusBar(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)
