import base64
import pickle
import zlib


class QResourceObject(object):
    def __init__(self, compressing: bool = True, encryption: bool = False) -> None:
        self._compressing = compressing
        self._encryption = encryption

        self._data = dict()

    def toDict(self) -> dict[str, object]:
        return self._data

    def toBytes(self) -> bytes:
        data = pickle.dumps(self._data)

        if self._compressing:
            data = zlib.compress(data)
        if self._encryption:
            data = base64.b64encode(data)

        data = bytearray(data)
        data.append(int(self._compressing))
        data.append(int(self._encryption))

        return bytes(data)

    def loadFromBytes(self, data: bytes, save_old: bool = False) -> None:
        raw = bytearray(data)
        data = bytes(raw[:-2])

        if not not raw[-1]:
            data = base64.b64decode(data)
        if not not raw[-2]:
            data = zlib.decompress(data)

        if save_old:
            self._data = {**self._data, **pickle.loads(data)}
        else:
            self._data = pickle.loads(data)

    def loadFromFile(self, path: str, save_old: bool = False) -> None:
        with open(path, mode="rb") as file:
            self.loadFromBytes(file.read(), save_old)

    def addResource(self, key: str, data: object) -> None:
        self._data[key] = data

    def getResource(self, key: str) -> object | bytes | None:
        if key in self._data:
            return self._data[key]
        return None

    def delResource(self, key: str) -> None:
        if key in self._data:
            del self._data[key]

    def save(self, path: str) -> None:
        with open(path, mode="wb") as file:
            file.write(self.toBytes())

    def __setitem__(self, key: str, value: object) -> None:
        return self.addResource(key, value)

    def __getitem__(self, item: str) -> object | bytes | None:
        return self.getResource(item)

    def __delitem__(self, key: str) -> None:
        return self.delResource(key)
