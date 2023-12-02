# import sys

from quof.methods.qanimations import QBaseWidgetAnimation
# from quof.gui.qstyle import QBaseStyle, QStyleLoader, qproperty
# from quof.widgets import QBaseMainWindow, QBaseApplication

# from PySide6.QtCore import QEvent
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QWidget, QFrame


class QBaseWidget(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._animation = QBaseWidgetAnimation(self)

    # def enterEvent(self, event: QEnterEvent) -> None:
    #     start = QStyleLoader.getProperty(
    #         f"{self.__class__.__name__}", "background", default=QColor(255, 255, 255, 255)
    #     ).value()
    #     end = QStyleLoader.getProperty(
    #         f"{self.__class__.__name__}:hover", "background", default=QColor(255, 255, 255, 255)
    #     ).value()
    #     transition = QStyleLoader.getProperty(
    #         f"{self.__class__.__name__}", "transition", default=3
    #     ).value()
    #
    #     # return backgroundColorAnimation(self, start, end, transition)
    #     return self._animation.backgroundColorAnimation(start, end, transition)
    #
    # def leaveEvent(self, event: QEvent) -> None:
    #     start = QStyleLoader.getProperty(
    #         f"{self.__class__.__name__}:hover", "background", default=QColor(255, 255, 255, 255)
    #     ).value()
    #     end = QStyleLoader.getProperty(
    #         f"{self.__class__.__name__}", "background", default=QColor(255, 255, 255, 255)
    #     ).value()
    #     transition = QStyleLoader.getProperty(
    #         f"{self.__class__.__name__}", "transition", default=3
    #     ).value()
    #
    #     # return backgroundColorAnimation(self, start, end, transition)
    #     return self._animation.backgroundColorAnimation(start, end, transition)
