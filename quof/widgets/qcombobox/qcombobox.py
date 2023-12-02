from PySide6.QtWidgets import QComboBox, QWidget


class QBaseComboBox(QComboBox):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
