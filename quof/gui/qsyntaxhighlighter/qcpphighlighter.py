from PySide6.QtCore import Qt
from PySide6.QtGui import QSyntaxHighlighter, QTextDocument


class QCppSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

    def highlightBlock(self, text: str) -> None:
        state = self.previousBlockState()
        start = 0

        if self.currentBlock().blockNumber() in list(range(10, 25)):
            self.currentBlock().setVisible(False)
        for index in range(len(text)):
            if state == 1 and text[index:index + 2] == "*/":
                state = -1
                self.setFormat(start, index - start + 2, Qt.GlobalColor.blue)
            else:
                if text[index:index + 2] == "//":
                    self.setFormat(index, len(text) - index, Qt.GlobalColor.red)
                elif text[index:index + 2] == "/*":
                    start = index
                    state = 1

        if state == 1:
            self.setFormat(start, len(text) - start, Qt.GlobalColor.blue)

        self.setCurrentBlockState(state)
