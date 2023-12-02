from PySide6.QtWidgets import QVBoxLayout, QWidget


class QBaseVBoxLayout(QVBoxLayout):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
