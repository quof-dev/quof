import os
import re
import string
import time

from .encdet import detect


def findInString(data: str, pattern: str, *, match_case: bool = True,
                 whole_words: bool = False, use_regex: bool = False) -> list[int]:

    if not match_case:
        data, pattern = data.lower(), pattern.lower()

    if use_regex:
        return [chunk.start(0) for chunk in re.finditer(pattern, data)]

    output = []
    splitter = string.whitespace + string.punctuation
    if pattern in data:
        first = pattern[0]
        for index, char in enumerate(data):
            if char == first and data[index:index + len(pattern)] == pattern:
                if whole_words and data[:index][-1] in splitter and data[index + len(pattern):][0] in splitter:
                    output.append(index)
                elif not whole_words:
                    output.append(index)

    return output


def findInFiles(directory: str, trigger: str, *, recursive: bool = True) -> dict[str, list[int]]:
    output = {}
    for path in os.listdir(directory):
        path = f"{directory}/{path}"
        if os.path.isdir(path) and recursive:
            output = {**output, **findInFiles(path, trigger)}
        else:
            with open(path, mode="rb") as file:
                data = file.read()
                output[path] = findInString(data.decode(detect(data)), trigger)

    return output


if __name__ == "__main__":
    start = time.time()
    findInFiles(r"D:\PyCharm\PythonProjects\Quof\application", "print")
    end = time.time()

    print(f"Completed for {end - start}s")
