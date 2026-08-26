from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256, sha3_256
import hmac
import re


_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)([^\s]+)"),
)


def redact_secrets(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(r"\1[REDACTED]", result)
    return result


def sha3_256_hex(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    return sha3_256(data).hexdigest()


def hmac_sha256_hex(key: bytes, data: bytes) -> str:
    if not isinstance(key, bytes) or not isinstance(data, bytes):
        raise TypeError("key and data must be bytes")
    if not key:
        raise ValueError("key must not be empty")
    return hmac.new(key, data, sha256).hexdigest()


def verify_hmac_sha256(key: bytes, data: bytes, expected_hex: str) -> bool:
    return hmac.compare_digest(hmac_sha256_hex(key, data), expected_hex)


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    object_lock_enabled: bool
    retain_days: int

    def __post_init__(self) -> None:
        if self.retain_days <= 0:
            raise ValueError("retain_days must be positive")


def verify_backup_manifest(files: dict[str, bytes], expected_hashes: dict[str, str]) -> tuple[str, ...]:
    failures: list[str] = []
    for path, expected in sorted(expected_hashes.items()):
        data = files.get(path)
        if data is None or sha256(data).hexdigest() != expected:
            failures.append(path)
    return tuple(failures)
