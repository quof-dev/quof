import typing

import collections.abc


def update(data: dict[str, typing.Any], new: dict[str, typing.Any] | typing.Any) -> dict[str, typing.Any]:
    for key, value in new.items():
        data[key] = update(data.get(key, {}), value) if isinstance(value, collections.abc.Mapping) else value
    return data


def get(data: dict[str, typing.Any], item: str) -> typing.Any:
    for key in item.split("."):
        data = data[key]

    return data
