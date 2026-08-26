from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()-]{7,}\d)(?!\d)")


@dataclass(frozen=True, slots=True)
class Redaction:
    start: int
    end: int
    kind: str


def detect_basic_contact_data(text: str) -> tuple[Redaction, ...]:
    findings: list[Redaction] = []
    for kind, pattern in (("email", _EMAIL_RE), ("phone", _PHONE_RE)):
        findings.extend(Redaction(match.start(), match.end(), kind) for match in pattern.finditer(text))
    return tuple(sorted(findings, key=lambda item: (item.start, item.end, item.kind)))


def redact_ranges(text: str, ranges: Iterable[Redaction], *, replacement: str = "[REDACTED]") -> str:
    ordered = sorted(ranges, key=lambda item: (item.start, item.end))
    cursor = 0
    output: list[str] = []
    for item in ordered:
        if item.start < cursor or item.start < 0 or item.end > len(text) or item.end < item.start:
            raise ValueError("redaction ranges must be valid and non-overlapping")
        output.append(text[cursor:item.start])
        output.append(replacement)
        cursor = item.end
    output.append(text[cursor:])
    return "".join(output)
