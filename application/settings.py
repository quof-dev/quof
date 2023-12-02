import functools
import sys
import typing

from quof.core import QText
from quof.widgets import (QBaseWidget, QBaseVBoxLayout,
                          QBasePushButton, QBaseScrollArea,
                          QBaseApplication, QBaseLabel,
                          QBaseCheckBox, QBaseComboBox)

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QWidget, QScrollArea


class ParagraphModel(QBaseWidget):

    class Models(object):
        CheckBox: None = 0
        List: None = 1

    def __init__(self, key: str, title: QText | str, type: int = 0,
                 params: typing.Any = None, default: typing.Any = None, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._key = key
        self._default = default

        self._label = QBaseLabel(title, self)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter
        )

        if type == ParagraphModel.Models.CheckBox:
            self._widget = QBaseCheckBox(self)
            self._widget.setChecked(default or True)
        elif type == ParagraphModel.Models.List:
            self._widget = QBaseComboBox(self)
            self._widget.addItems(params)

        self.setFixedHeight(40)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._label.resize(self.width() // 2, self.height())

        self._widget.move(self.width() // 2, 0)
        self._widget.resize(self.width() // 2, self.height())


class Paragraph(QBaseWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._params_widget = QBaseWidget(self)

        self._params = QBaseVBoxLayout(self._params_widget)
        self._params.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidget(self._params_widget)
        self._scroll_area.setWidgetResizable(True)

    def addParam(self, model: ParagraphModel) -> None:
        self._params.addWidget(model, 1)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._scroll_area.resize(self.size())


class Settings(QBaseWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._paragraphs = []

        self._titles_widget = QBaseWidget(self)

        self._titles = QBaseVBoxLayout(self._titles_widget)
        self._titles.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidget(self._titles_widget)
        self._scroll_area.setWidgetResizable(True)

        self._settings = QBaseWidget(self)

    def addParagraph(self, title: QText | str, paragraph: Paragraph) -> None:
        self._paragraphs.append((title, paragraph))

        button = QBasePushButton(title)
        button.pressed.connect(  # noqa
            functools.partial(self.switchParagraph, len(self._paragraphs) - 1)
        )

        paragraph.setParent(self._settings)

        self._titles.addWidget(button)

    def switchParagraph(self, index: int) -> None:
        self._paragraphs[index][1].raise_()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._scroll_area.resize(
            self.width() // 4, self.height()
        )

        self._settings.setGeometry(
            QRect(self.width() // 4, 0, self.width() - (self.width() // 4), self.height())
        )

        for _, widget in self._paragraphs:
            widget.resize(self._settings.size())

        return super().resizeEvent(event)


if __name__ == "__main__":
    app = QBaseApplication(sys.argv)
    app.setStyleSheet(
        "QBaseWidget {"
        "   background: #222222;"
        "}"
        "Settings QBasePushButton {"
        "   color: white;"
        "   background: #282828;"
        "   border: none;"
        "   border-radius: 5px;"
        "   padding: 7px;"
        "}"
        "Settings QBasePushButton:hover {"
        "   background: #202020;"
        "}"
        "Settings QBasePushButton:pressed {"
        "   background: #323232;"
        "}"
        "Settings QBaseScrollArea {"
        "   border: none;"
        "}"
    )

    main = Settings()

    p1 = Paragraph()
    p1.addParam(ParagraphModel("syntax-highlight", "Syntax Highlight"))
    p2 = Paragraph()

    main.addParagraph("First", p1)
    main.addParagraph("Second", p2)
    for _ in range(10):
        main.addParagraph("Test", Paragraph())

    main.resize(400, 300)
    main.show()

    sys.exit(app.exec())
