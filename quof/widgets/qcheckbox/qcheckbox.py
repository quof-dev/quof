from PySide6.QtWidgets import QCheckBox, QWidget


class QBaseCheckBox(QCheckBox):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
