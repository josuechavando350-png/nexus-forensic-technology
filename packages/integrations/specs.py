from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class RequestSpec:
    method: str
    url: str
    headers: tuple[tuple[str, str], ...] = ()
    body: bytes | None = None

    def __post_init__(self) -> None:
        method = self.method.upper()
        if method not in {"GET", "POST"}:
            raise ValueError("method must be GET or POST")
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP(S) URL")
        object.__setattr__(self, "method", method)


@dataclass(frozen=True, slots=True)
class CommandSpec:
    argv: tuple[str, ...]
    read_only: bool = True

    def __post_init__(self) -> None:
        if not self.argv or not self.argv[0].strip():
            raise ValueError("argv must contain an executable")
        if any("\x00" in item for item in self.argv):
            raise ValueError("argv entries must not contain NUL bytes")


def require_nonblank(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must not be blank")
    return cleaned


def require_safe_local_path(path: str, field: str = "path") -> str:
    cleaned = require_nonblank(path, field)
    if "\x00" in cleaned:
        raise ValueError(f"{field} must not contain NUL bytes")
    return str(PurePath(cleaned))
