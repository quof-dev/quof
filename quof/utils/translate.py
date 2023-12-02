import functools
import html
import re

import urllib.request
import urllib.parse


@functools.cache
def translate(text: str, *, to_lang: str = "auto", from_lang: str = "auto", save_spaces: bool = True) -> str:
    """ A function to translate text from one language to another. """

    output = ""
    if save_spaces:
        text = text.replace("!", "\\!").replace("\n", " !! ")

    if len(text) > 5000:
        raise Exception("The length of the text exceeds 5000 characters!")

    request = urllib.request.Request(
        f"http://translate.google.com/m?tl={to_lang}&sl={from_lang}&q={urllib.parse.quote(text)}"
    )
    result = re.findall(
        r"(?s)class=\"(?:t0|result-container)\">(.*?)<",
        urllib.request.urlopen(request).read().decode("utf-8")
    )

    if result:
        output = html.unescape(result[0])

    return output.replace(" !! ", "\n").replace("\\!", "!") if save_spaces else output
