"""Unicode tokenization and deliberately simple sentence boundaries."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

BOUNDARY = re.compile(r"[.!?]+(?:[\"”’']*)(?=\s|$)")


def normal(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold().replace("’", "'")


@dataclass(frozen=True)
class Token:
    surface: str
    normalized: str
    start: int
    end: int


@dataclass(frozen=True)
class Sentence:
    id: str
    text: str
    start: int
    end: int
    tokens: tuple[Token, ...]


def tokens(text: str, offset: int = 0) -> tuple[Token, ...]:
    # Python's \w omits combining marks. Scan Unicode categories without rewriting
    # input so canonically equivalent forms retain their original span offsets.
    result = []
    i = 0
    while i < len(text):
        if unicodedata.category(text[i])[0] not in "LN":
            i += 1
            continue
        start = i
        i += 1
        while i < len(text):
            if unicodedata.category(text[i])[0] in "LNM":
                i += 1
            elif (text[i] in "'’" and i + 1 < len(text)
                  and unicodedata.category(text[i + 1])[0] in "LN"):
                i += 1
            else:
                break
        surface = text[start:i]
        result.append(Token(surface, normal(surface), offset + start, offset + i))
    return tuple(result)


def sentences(text: str, doc_id: str = "doc") -> list[Sentence]:
    """Keep offsets in input text. Abbreviations/quoted punctuation require audit."""
    spans = []
    start = 0
    for match in BOUNDARY.finditer(text):
        # A numeral followed by a period can be a verse/list label, not a sentence.
        if re.fullmatch(r"\s*\d+", text[start:match.start()]):
            continue
        spans.append((start, match.end()))
        start = match.end()
    if text[start:].strip():
        spans.append((start, len(text)))
    result = []
    for a, b in spans:
        segment = text[a:b]
        a += len(segment) - len(segment.lstrip())
        b -= len(segment) - len(segment.rstrip())
        if a < b and tokens(text[a:b]):
            result.append(Sentence(f"{doc_id}:s{len(result):04d}", text[a:b], a, b, tokens(text[a:b], a)))
    return result
