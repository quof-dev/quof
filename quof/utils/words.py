import math
import re


def count_words(text: str) -> int:
    return len(re.findall(r"\W+", text))


def selects_words(text: str) -> list[tuple[int, int]]:
    return [(chunk.start(), chunk.end()) for chunk in re.finditer(r"\W+", text)]


def read_time(text: str, wpm: int = 200) -> int:
    return math.ceil(count_words(text) / wpm * 60)


with open(r"C:\Users\Никита\Downloads\соч.txt", mode="r", encoding="utf-8") as file:
    print(count_words(file.read()))
