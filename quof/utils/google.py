import functools
import requests
import urllib.parse

from bs4 import BeautifulSoup


@functools.cache
def search(query: str, *, results: int = 15) -> list[tuple[str, str]]:
    """ Function to search for a custom query. """

    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={results}"
    parser = BeautifulSoup(requests.get(url).content, "html.parser")

    output = []
    for link in parser.find_all("a"):
        href = link.get("href")
        if "url?q=" not in href or "webcache" in href:
            continue

        if title := link.find_all("h3"):
            output.append((title[0].getText(), href.split("?q=")[1].split("&sa=U")[0]))

    return output
