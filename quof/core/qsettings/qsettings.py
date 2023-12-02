import typing

from quof.utils import dictionary, profiler


class QSettingLoader(object):
    def __init__(self, application: str, company: str = None) -> None:
        self._path = profiler.createUserAppFolder(application, company)

    def __getitem__(self, item: str) -> typing.Any:
        return dictionary.get(profiler.readSettings(self._path), item)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        profiler.updateSettings(self._path, value)


print(QSettingLoader("Quof")["data"])
