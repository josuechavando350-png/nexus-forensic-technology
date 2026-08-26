from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
import re
import unicodedata


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(_TOKEN_RE.findall(normalized))


def token_frequencies(text: str) -> dict[str, int]:
    normalized = normalize_text(text)
    return dict(Counter(normalized.split())) if normalized else {}


def cosine_text_similarity(left: str, right: str) -> float:
    a = token_frequencies(left)
    b = token_frequencies(right)
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b.get(token, 0) for token in a)
    norm_a = sqrt(sum(value * value for value in a.values()))
    norm_b = sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b)


@dataclass(frozen=True, slots=True)
class Stylometry:
    characters: int
    words: int
    sentences: int
    average_word_length: float

    @classmethod
    def from_text(cls, text: str) -> "Stylometry":
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        words = _TOKEN_RE.findall(text)
        sentences = len(re.findall(r"[.!?]+", text))
        avg = (sum(len(word) for word in words) / len(words)) if words else 0.0
        return cls(len(text), len(words), sentences, avg)


def scam_script_overlap(text: str, phrases: tuple[str, ...]) -> tuple[str, ...]:
    normalized = normalize_text(text)
    matches = []
    for phrase in phrases:
        candidate = normalize_text(phrase)
        if candidate and candidate in normalized:
            matches.append(phrase)
    return tuple(matches)
