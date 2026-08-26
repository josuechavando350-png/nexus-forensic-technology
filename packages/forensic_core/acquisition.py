from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AcquisitionRecord:
    source_path: str
    size_bytes: int
    sha256_hex: str


def hash_file_read_only(path: str | Path, *, chunk_size: int = 1024 * 1024) -> AcquisitionRecord:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError("path must reference an existing regular file")
    digest = sha256()
    size = 0
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return AcquisitionRecord(str(file_path), size, digest.hexdigest())
