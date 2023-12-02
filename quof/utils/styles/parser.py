import json
import os

from function import function
from structure import StructMeta, Struct


def loads(string: str) -> ...:
    data = json.loads(string)

    plugins = {}
    if "includes" in data:
        for library in data["includes"]:
            if library in StructMeta.data():
                plugins.update(
                    **StructMeta.data()[library]
                )

    sources = {}
    if "sources" in data:
        for key, path in data["sources"].items():
            if not os.path.exists(path):
                continue

            with open(path, mode="rb") as file:
                sources[key] = file.read()

    classes = {}
    if "classes" in data:
        for name, struct in data["classes"].items():
            style = {}
            for selector, declaration in struct.items():
                propertys = {}
                for key, value in declaration.items():
                    parsed = function(
                        key, value, plugins=plugins
                    )

                    propertys[parsed["key"]] = parsed["return"]

                style[selector] = propertys
            classes[name] = style

    return classes


class Qt6(Struct):
    @staticmethod
    def integer(value: str) -> object:
        return int(value)


with open(r"D:\PyCharm\PythonProjects\Quof\application\resources\styles\light.style.struct.json") as file_:
    print(loads(file_.read()))
