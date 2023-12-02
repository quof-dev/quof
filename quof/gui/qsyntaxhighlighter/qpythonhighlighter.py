from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name

from PySide6.QtCore import Qt
from PySide6.QtGui import QSyntaxHighlighter, QTextDocument, QColor


def color(chex: str):
    return QColor(int(chex[0:2], 16), int(chex[2:4], 16), int(chex[4:6], 16))


class QPythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        self._lexer = get_lexer_by_name("python")
        self._formatter = get_style_by_name("dracula").styles

        self._previous_text = ""
        self._previous_highlight = []
        self._previous_index = 0

    def highlightBlock(self, text: str) -> None:
        data = self._lexer.get_tokens_unprocessed(self.document().toPlainText())
        for index, style, chunk in data:
            if style in self._formatter:
                formatter = color(self._formatter[style].split()[0][1:])
            else:
                formatter = Qt.GlobalColor.white

            self.setFormat(index, len(chunk), formatter)

        state = self.previousBlockState()
        start = 0

        for index in range(len(text)):
            if state == 1 and text[index:index + 3] == "\"\"\"":
                state = -1
                self.setFormat(start, index - start + 3, Qt.GlobalColor.blue)
            else:
                if text[index] == "#":
                    self.setFormat(index, len(text) - index, Qt.GlobalColor.red)
                elif text[index:index + 3] == "\"\"\"":
                    start = index
                    state = 1

        if state == 1:
            self.setFormat(start, len(text) - start, Qt.GlobalColor.blue)

        self.setCurrentBlockState(state)
