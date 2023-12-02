import typing

from quof.utils import qss

from PySide6.QtGui import QColor


class qproperty(object):
    def __init__(self, value: object, wrap: str = "", serializer: typing.Callable[[typing.Any], str] = str) -> None:
        self._value = value
        self._wrap = wrap

        self._serializer = serializer

    def value(self) -> typing.Any:
        return self._value

    def serialize(self) -> str:
        return f"{self._wrap}({self._serializer(self._value)})" if self._wrap else self._serializer(self._value)

    @classmethod
    def integer(cls, value: int) -> "qproperty":
        return qproperty(value=value)

    @classmethod
    def color(cls, color: str | tuple[float, ...] | QColor) -> "qproperty":
        return qproperty(
            value=(QColor(*color) if isinstance(color, tuple) or isinstance(color, list) else QColor(color)),
            wrap="rgba", serializer=lambda obj: str(obj.getRgb())[1:-1]
        )

    @classmethod
    def radius(cls, radius: int | float) -> "qproperty":
        return qproperty(value=radius)

    @classmethod
    def px(cls, pixels: int | float) -> "qproperty":
        return qproperty(value=pixels, serializer=lambda obj: f"{obj}px")

    @classmethod
    def url(cls, link: str) -> "qproperty":
        return qproperty(value=link, wrap="url")

    @classmethod
    def margin(cls, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> "qproperty":
        return qproperty(
            value=(top, right, bottom, left), serializer=lambda obj: " ".join([f"{pixel}px" for pixel in obj])
        )

    @classmethod
    def border(cls, width: int, background: str = "transparent", color: str = "black") -> "qproperty":
        return qproperty(
            value=(width, background, color), serializer=lambda obj: f"{obj[0]}px {obj[1]} {obj[2]}"
        )

    @classmethod
    def none(cls, _: object = None) -> "qproperty":
        return qproperty(value=None, serializer=lambda _: "none")

    @classmethod
    def unknown(cls, value: object, wrap: str = "") -> "qproperty":
        return qproperty(value=value, wrap=wrap)

    def __repr__(self) -> str:
        return self.serialize()


class QStyle(object):
    _storage = {}
    _marked = {}

    @classmethod
    def storage(cls) -> dict[str, dict[str, typing.Any]]:
        return cls._storage

    @classmethod
    def marked(cls) -> dict[str, str]:
        return cls._marked

    @classmethod
    def get(cls, path: str, default: typing.Any = None) -> typing.Any | None:
        selector, key = path.split("->")

        if selector in cls._storage and key in cls._storage[selector]:
            return cls._storage[selector][key]["cast"]

        return default

    @classmethod
    def markAs(cls, selector: str, new: str) -> None:
        declaration = cls._storage.pop(selector)

        cls._storage[selector] = declaration
        cls._storage[new] = selector

    @classmethod
    def markAsCustom(cls, path: str) -> None:
        selector, key = path.split("->")

        if selector in cls._storage and key in cls._storage[selector]:
            cls._storage[selector][key]["custom"] = True

    @classmethod
    def cast(cls, name: str, arguments: typing.Any) -> typing.Any:
        match name:
            case "color":
                if isinstance(arguments, tuple) or isinstance(arguments, list):
                    return QColor(*arguments)
                else:
                    return QColor(arguments)
            case _:
                return arguments

    @classmethod
    def loadFromFile(cls, path: str, overwrite: bool = True) -> None:
        if overwrite:
            cls._storage = {}

        for selectors, declaration in qss.loads(path).items():
            for selector in selectors:
                for key, value in declaration.items():
                    if selector not in cls._storage:
                        cls._storage[selector] = {}

                    cls._storage[selector][key] = {
                        "cast": cls.cast(value["name"], value["arguments"]),
                        "serialized": value["serialized"],
                        "custom": False
                    }
