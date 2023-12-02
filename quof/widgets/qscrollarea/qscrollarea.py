from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QScrollArea, QWidget, QApplication


class QBaseScrollArea(QScrollArea):

    class SmoothMove(object):
        NoSmooth = 0x0001
        Cosine = 0x0002

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._last_wheel = None

        self._smooth_timer = QTimer(self)
        self._smooth_timer.timeout.connect(
            self.slotSmoothMove
        )

        self._fps = 60
        self._duration = 400
        self._mode = self.SmoothMove.Cosine
        self._acceleration = 2.5

        self._small_step_modifier = Qt.KeyboardModifier.ShiftModifier
        self._small_step_ratio = 0.2
        self._big_step_modifier = Qt.KeyboardModifier.AltModifier
        self._big_step_ratio = 5.0

        self._steps_left_queue = []

    def subDelta(self, delta: float, steps: int) -> float:
        return 0

    def slotSmoothMove(self) -> None:
        total_delta = 0

        for index, item in enumerate(self._steps_left_queue):
            total_delta += self.subDelta(item[0], item[1])

            self._steps_left_queue[index][0] -= 1

        while self._steps_left_queue and self._steps_left_queue[0][1] == 0:
            self._steps_left_queue.pop(0)

        orientation = self._last_wheel.angleDelta().x()

        if (self._big_step_modifier & Qt.KeyboardModifier.AltModifier) or (self._small_step_modifier & Qt.KeyboardModifier.AltModifier):
            orientation = Qt.Orientation.Vertical

        event = QWheelEvent(
            self._last_wheel.pos(),
            self._last_wheel.globalPos(),
            round(total_delta),
            self._last_wheel.buttons(),
            0,
            orientation
        )

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._mode == self.SmoothMove.NoSmooth:
            return super().wheelEvent(event)

        scroll_stamps = []
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        scroll_stamps.append(now)

        while now - scroll_stamps[0] > 500:
            scroll_stamps.pop(0)

        acceleration_ratio = min(len(scroll_stamps) / 15, 1)

        if not self._last_wheel:
            self._last_wheel = QWheelEvent(event)

        steps_total = self._fps * self._duration / 1000
        multiplier = 1

        if QApplication.keyboardModifiers() & self._small_step_modifier:
            multiplier *= self._small_step_ratio
        if QApplication.keyboardModifiers() & self._big_step_modifier:
            multiplier *= self._big_step_ratio

        delta = max(event.pixelDelta().toTuple()) * multiplier

        if self._acceleration > 0:
            delta += delta * self._acceleration * acceleration_ratio

        self._steps_left_queue.append([delta, steps_total])

        self._smooth_timer.start(1000 // self._fps)
