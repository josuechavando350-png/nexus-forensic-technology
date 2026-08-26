from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import Mapping


@dataclass(frozen=True, slots=True)
class PackageEntry:
    path: str
    size_bytes: int
    sha256_hex: str

    def __post_init__(self) -> None:
        path = PurePosixPath(self.path)
        if path.is_absolute() or ".." in path.parts or self.path in {"", "."}:
            raise ValueError("package path must be a safe relative POSIX path")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if len(self.sha256_hex) != 64:
            raise ValueError("sha256_hex must be a SHA-256 digest")
        try:
            bytes.fromhex(self.sha256_hex)
        except ValueError as exc:
            raise ValueError("sha256_hex must be valid hexadecimal") from exc


def build_package_manifest(files: Mapping[str, bytes]) -> tuple[PackageEntry, ...]:
    entries = []
    for path, data in sorted(files.items()):
        if not isinstance(data, bytes):
            raise TypeError("package file contents must be bytes")
        entries.append(PackageEntry(path, len(data), sha256(data).hexdigest()))
    return tuple(entries)


def manifest_bytes(entries: tuple[PackageEntry, ...]) -> bytes:
    payload = [{"path": entry.path, "sha256": entry.sha256_hex, "size": entry.size_bytes} for entry in sorted(entries, key=lambda item: item.path)]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
