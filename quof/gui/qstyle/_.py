class QStyleObject(object):
    def __init__(self, name: str, path: list[str] = None, values: dict[str, qproperty] = None) -> None:
        self._name = name
        self._path = path or []

        self._values = values or {}

    def values(self) -> dict[str, qproperty]:
        return self._values

    def setValues(self, **values: qproperty) -> None:
        self._values.update(**{key.replace("-", "_"): value for key, value in values.items()})


class QStylesStorage(object):
    def __init__(self) -> None:
        self._storage = {}

    def existStyle(self, storage: str, name: str) -> bool:
        return storage in self._storage and name in self._storage[storage]

    def getSelector(self, storage: str, name: str, default: typing.Any = None) -> QStyleObject | None:
        if self.existStyle(storage, name):
            return self._storage[storage][name]

        if isinstance(default, QStyleObject):
            return self.registerStyle(storage, name, default)

        return default

    def getStyle(self, storage: str) -> dict[str, QStyleObject]:
        return self._storage[storage] if storage in self._storage else {}

    def registerStyle(self, storage: str, name: str, style: QStyleObject) -> QStyleObject:
        if storage not in self._storage:
            self._storage[storage] = {}
        self._storage[storage][name] = style

        return style


class QBaseStyleMeta(type):
    _styles = QStylesStorage()

    def storage(cls) -> QStylesStorage:
        return cls._styles

    def name(cls) -> str:
        return vars(cls)["__stylename__"] if "__stylename__" in vars(cls) else cls.__name__

    def __getitem__(cls, item: str) -> QStyleObject:
        data = item.split(":")

        style = QStyleObject(data[0], []) if len(data) == 1 else QStyleObject(data[0], data[1:])
        style_storage = QBaseStyleMeta._styles.getSelector(
            vars(cls)["__stylename__"] if "__stylename__" in vars(cls) else cls.__name__, item, style
        )

        return style_storage


class QBaseStyle(object, metaclass=QBaseStyleMeta):
    __stylename__ = "base-style"

    @classmethod
    def styles(cls) -> None:
        ...

    @classmethod
    def loadFromFile(cls, path: str, encoding: str = "utf-8") -> None:
        for selectors, declaration in qss.loads(path).items():
            for rule, value in declaration.items():
                for selector in selectors:
                    if hasattr(qproperty, value["name"]):
                        cls[selector].setValues(
                            **{rule: getattr(qproperty, value["name"])(value["arguments"])}
                        )
                    else:
                        cls[selector].setValues(
                            **{rule: qproperty(
                                value["arguments"], serializer=lambda _: value["serialized"]
                            )}
                        )
