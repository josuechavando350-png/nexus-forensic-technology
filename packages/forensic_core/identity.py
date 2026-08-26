from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata


def normalize_identity_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("value must be str")
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    lowered = ascii_text.casefold()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


@dataclass(frozen=True, slots=True)
class IdentityMatch:
    left: str
    right: str
    score: float
    method: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")


def compare_identity_text(left: str, right: str) -> IdentityMatch:
    left_norm = normalize_identity_text(left)
    right_norm = normalize_identity_text(right)
    if not left_norm or not right_norm:
        return IdentityMatch(left, right, 0.0, "empty")
    if left_norm == right_norm:
        return IdentityMatch(left, right, 1.0, "normalized-exact")
    score = SequenceMatcher(None, left_norm, right_norm, autojunk=False).ratio()
    return IdentityMatch(left, right, score, "sequence-ratio")


def is_candidate_match(match: IdentityMatch, *, threshold: float = 0.90) -> bool:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    return match.score >= threshold
