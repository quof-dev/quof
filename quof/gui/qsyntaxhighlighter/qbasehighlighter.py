import re

from quof.gui.qstyle import QStyle

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument


class QHighlighterCharFormat(QTextCharFormat):
    def __init__(self, color: QColor | Qt.GlobalColor = QColor(0, 0, 0, 255),
                 background: QColor | Qt.GlobalColor = QColor(0, 0, 0, 0),
                 weight: QFont.Weight = QFont.Weight.Normal) -> None:

        super().__init__()

        self.setForeground(color)
        self.setBackground(background)
        self.setFontWeight(weight)


class QHighlighterColorScheme(object):
    textFormat = QHighlighterCharFormat()

    keywordFormat = QHighlighterCharFormat(Qt.GlobalColor.darkBlue, weight=QFont.Weight.Bold)
    classFormat = QHighlighterCharFormat(Qt.GlobalColor.darkMagenta, weight=QFont.Weight.Bold)
    functionFormat = QHighlighterCharFormat(Qt.GlobalColor.blue)
    quoteFormat = QHighlighterCharFormat(Qt.GlobalColor.darkGreen)
    inlineCommentFormat = QHighlighterCharFormat(Qt.GlobalColor.darkGreen)
    blockCommentFormat = QHighlighterCharFormat(Qt.GlobalColor.darkGreen)


class QBaseSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

    def highlightWhitespaces(self, text: str) -> None:
        whitespace_color = QColor(QStyle.get(
            "QBaseTextEdit->whitespace-color", default=Qt.GlobalColor.lightGray
        ))
        whitespace_color.setAlphaF(0.15)

        formatter = QTextCharFormat()
        formatter.setForeground(whitespace_color)

        for match in re.finditer(r"\s+", text):
            self.setFormat(
                match.start(), len(match.group(0)), formatter
            )

    def highlightBlock(self, text: str) -> None:
        self.highlightWhitespaces(text)


class QBaseSyntaxHighlighter_(QSyntaxHighlighter):
    class BlockState(object):
        NotInComment = 0
        InComment = 1

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        self._color_scheme = QHighlighterColorScheme

        self._rules = []
        self._comment_start = "/*"
        self._comment_end = "*/"

    def addKeywords(self, keywords: list[str]) -> None:
        for keyword in keywords:
            self.addRule(QRegularExpression(rf"\b{keyword}\b"), self._color_scheme.keywordFormat)

    def addRule(self, rule: QRegularExpression, formatter: QHighlighterCharFormat) -> None:
        self._rules.append((rule, formatter))

    def highlightBlock(self, text: str) -> None:
        for regex, formatter in self._rules:
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), formatter)

        self.setCurrentBlockState(QBaseSyntaxHighlighter_.BlockState.NotInComment)
        self.highlightMultilineComments(text)

    def highlightMultilineComments(self, text: str) -> None:
        ...
