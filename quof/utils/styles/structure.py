import typing


class StructMeta(type):
    _data = {}

    def __new__(cls, name: str, bases: tuple[type, ...], data: dict[str, typing.Any]) -> type:
        functions = {}
        for key, value in data.items():
            if callable(value):
                functions[key] = value

        cls._data[name.lower()] = functions

        return super().__new__(cls, name, bases, data)

    @classmethod
    def data(cls) -> dict[str, dict[str, typing.Callable]]:
        return cls._data


class Struct(object, metaclass=StructMeta):
    ...
