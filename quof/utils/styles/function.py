import re
import typing


def function(key: str, values: dict[str, typing.Any], *, plugins: dict[str, callable] = None) -> dict[str, typing.Any]:
    name, type = re.findall(r"(.*)\[(.*?)\]", key)[-1]  # noqa

    if plugins is None:
        plugins = []

    if type in plugins:
        if "*" in values:
            keywords = values.copy()
            keywords.pop("*")

            return {"key": name, "type": type, "return": plugins[type](*values["*"], **keywords)}
        else:
            return {"key": name, "type": type, "return": plugins[type](**values)}

    return {"key": name, "type": type, "return": None}
