import typing

from quof.gui import QStyleLoader
from quof.core import QLocalizationLoader

from PySide6.QtWidgets import QApplication


class QBaseApplication(QApplication):
    _instance = None

    def __new__(cls, *args: typing.Any, **kwargs: typing.Any) -> None:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, argv: list[str], style: str = None, locale: str = None) -> None:
        super().__init__(argv)

        self._style_loader = QStyleLoader(self, style)
        if style:
            self._style_loader.load()

        self._locale_loader = QLocalizationLoader(locale)
        if locale:
            self._locale_loader.load()

    @classmethod
    def instance(cls) -> "QBaseApplication":
        return cls._instance

    def styleLoader(self) -> QStyleLoader:
        return self._style_loader

    def localeLoader(self) -> QLocalizationLoader:
        return self._locale_loader
