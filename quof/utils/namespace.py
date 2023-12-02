class NamespaceMeta(type):
    def __new__(cls, name: str, base: tuple[type, ...], data: dict[str, object]) -> type:
        namespace = {}
        for key, value in data.items():
            if not key.startswith("_"):
                namespace[key] = value

        namespace_class = super().__new__(cls, name, base, data)
        namespace_class._namespace = namespace

        return namespace_class

    def __contains__(cls, item: object) -> bool:
        return item in cls._namespace.values()


class Namespace(object, metaclass=NamespaceMeta):
    _namespace: dict[str, object]


class Test(Namespace):
    test: str = "123"


print(Test.test)
