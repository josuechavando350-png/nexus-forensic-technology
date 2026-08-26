from __future__ import annotations

from hashlib import sha256
from typing import Iterable


def _leaf_hash(data: bytes) -> bytes:
    if not isinstance(data, bytes):
        raise TypeError("leaf data must be bytes")
    return sha256(b"\x00" + data).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return sha256(b"\x01" + left + right).digest()


def merkle_root_hex(leaves: Iterable[bytes]) -> str:
    level = [_leaf_hash(leaf) for leaf in leaves]
    if not level:
        return sha256(b"").hexdigest()
    while len(level) > 1:
        next_level: list[bytes] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(_node_hash(left, right))
        level = next_level
    return level[0].hex()
