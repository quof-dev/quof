import os

from quof.core.qsignal import QSignal

from quof.utils import localization


class QLocalizationLoader(object):
    _instance = None

    localeChanged = QSignal()

    def __new__(cls, *args, **kwargs) -> type:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, directory: str, extension: str = ".lang") -> None:
        self._directory = directory
        self._extension = extension

        self._localizations = {}
        self._current = {}

    @classmethod
    def instance(cls) -> "QLocalizationLoader":
        return cls._instance

    @classmethod
    def getText(cls, key: str) -> str:
        if instance := cls.instance():
            return instance._current.get(key, key)

        return key

    def locale(self) -> dict[str, str]:
        return self._current

    def load(self, language: str = "en") -> None:
        for path in os.listdir(self._directory):
            if path.endswith(self._extension):
                self._localizations[path[:-len(self._extension)]] = localization.loads(
                    os.path.join(self._directory, path)
                )

        self._current = self._localizations.get(language, {})

    def setLocale(self, language: str) -> None:
        self._current = self._localizations.get(language, {})

        self.localeChanged.emit(language)


class QText(object):
    def __init__(self, key: str) -> None:
        self._key = key

        self.textChanged = QSignal()
        QLocalizationLoader.localeChanged.connect(
            lambda _: self.textChanged.emit()
        )

    @classmethod
    def get(cls, key: str) -> str:
        return QLocalizationLoader.getText(key)

    def text(self) -> str:
        return QLocalizationLoader.getText(self._key)
