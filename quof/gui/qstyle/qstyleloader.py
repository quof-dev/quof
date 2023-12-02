from .qbasestyle import QStyle

from PySide6.QtWidgets import QApplication


class QStyleLoader(object):
    _instance = None

    def __new__(cls, *args, **kwargs) -> type:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, application: QApplication, path: str = None) -> None:
        self._application = application
        self._path = path

        if self._path:
            QStyle.loadFromFile(self._path)

        self.load()

    @classmethod
    def instance(cls) -> "QStyleLoader":
        return cls._instance

    def update(self, path: str) -> None:
        self._path = path
        if self._path:
            QStyle.loadFromFile(self._path)

        self.load()

    def load(self) -> None:
        delimiter = "\n"

        data = []
        for selector, declaration in QStyle.storage().items():
            if declaration.values():
                styles = []
                for key, value in declaration.items():
                    if not value["custom"]:
                        styles.append(f"    {key}: {value['serialized']};")
                    else:
                        print(value)

                data.append(f"{QStyle.marked().get(selector, selector)} {{\n{delimiter.join(styles)}\n}}")

        self._application.setStyleSheet("\n".join(data))
