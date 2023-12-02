from PySide6.QtCore import QPropertyAnimation, QParallelAnimationGroup
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget


def backgroundColorAnimation(widget: QWidget, start: QColor, end: QColor, transition: int = 3) -> None:
    def _setColor(value: QColor) -> None:
        widget.setStyleSheet(f"{widget.__class__.__name__} {{ background: rgba{value.getRgb()} }}")

    animation = QPropertyAnimation(widget)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setDuration(transition * 100)
    animation.valueChanged.connect(_setColor)  # noqa
    animation.start()


class QBaseWidgetAnimation(object):
    def __init__(self, widget: QWidget) -> None:
        self._widget = widget

        self._storage = {}
        self._animation = None

    def _deleteAnimationGroup(self) -> None:
        self._animation = None

    def _createAnimationGroup(self) -> QParallelAnimationGroup:
        if self._animation is None:
            self._animation = QParallelAnimationGroup()
            self._animation.finished.connect(self._deleteAnimationGroup)

        return self._animation

    def backgroundColorAnimation(self, start: QColor, end: QColor, transition: int = 3, storage: bool = True) -> None:
        def _setColor(value: QColor) -> None:
            self._widget.setStyleSheet(
                f"{self._widget.__class__.__name__} {{ background: rgba{value.getRgb()} }}"
            )

        if storage and "background" in self._storage:
            start = self._storage["background"]
            self._storage["background"] = end

        animation = QPropertyAnimation(self._widget)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setDuration(transition * 100)
        animation.valueChanged.connect(_setColor)  # noqa
        animation.start()
