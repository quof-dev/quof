import json
import os
import typing

from .serializer import ResourceObject

from quof.utils import dictionary


def createUserAppFolder(application: str, company: str = None, cache: bool = True, logs: bool = True,
                        resources: bool = True, downloads: bool = True, settings: bool = True) -> str:
    path = f"{os.getenv('localappdata')}\\{application}"
    if company:
        path = f"{os.getenv('localappdata')}\\{company}\\{application}"

    if cache:
        os.makedirs(f"{path}\\cache", exist_ok=True)
    if logs:
        os.makedirs(f"{path}\\logs", exist_ok=True)
    if resources:
        os.makedirs(f"{path}\\resources", exist_ok=True)
    if downloads:
        os.makedirs(f"{path}\\downloads", exist_ok=True)
    if settings and not os.path.exists(f"{path}\\settings.json"):
        open(f"{path}\\settings.json", mode="w", encoding="utf-8").close()

    return path


def updateSettings(path: str, data: dict[str, typing.Any], overwrite: bool = False) -> None:
    path = f"{path}\\settings.json"

    if overwrite and os.path.exists(path):
        with open(path, mode="r", encoding="utf-8") as file:
            data = dictionary.update(data, json.loads(file.read()))

    with open(path, mode="w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False, indent=4))


def readSettings(path: str) -> dict[str, typing.Any]:
    with open(f"{path}\\settings.json", mode="r", encoding="utf-8") as file:
        return json.loads(file.read())
