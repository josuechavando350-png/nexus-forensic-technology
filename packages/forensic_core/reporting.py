from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


def deterministic_report_bytes(report: dict[str, Any]) -> bytes:
    if not isinstance(report, dict):
        raise TypeError("report must be a dict")
    return json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def report_sha256(report: dict[str, Any]) -> str:
    return sha256(deterministic_report_bytes(report)).hexdigest()
