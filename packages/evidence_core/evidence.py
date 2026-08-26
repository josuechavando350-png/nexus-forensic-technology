from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    source_ref: str
    sha256_hex: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be blank")
        if not self.source_ref.strip():
            raise ValueError("source_ref must not be blank")
        if len(self.sha256_hex) != 64:
            raise ValueError("sha256_hex must contain exactly 64 hexadecimal characters")
        try:
            bytes.fromhex(self.sha256_hex)
        except ValueError as exc:
            raise ValueError("sha256_hex must be valid hexadecimal") from exc
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be greater than or equal to zero")


def sha256_hex(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    return sha256(data).hexdigest()


def create_evidence_record(*, evidence_id: str, source_ref: str, data: bytes) -> EvidenceRecord:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    return EvidenceRecord(
        evidence_id=evidence_id,
        source_ref=source_ref,
        sha256_hex=sha256_hex(data),
        size_bytes=len(data),
    )


def verify_evidence_bytes(record: EvidenceRecord, data: bytes) -> bool:
    if not isinstance(record, EvidenceRecord):
        raise TypeError("record must be an EvidenceRecord")
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) != record.size_bytes:
        return False
    return compare_digest(sha256_hex(data), record.sha256_hex)
