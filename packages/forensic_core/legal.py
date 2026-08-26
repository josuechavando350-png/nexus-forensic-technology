from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class LegalBasis:
    jurisdiction: str
    authority: str
    purpose: str
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.jurisdiction.strip() or not self.authority.strip() or not self.purpose.strip():
            raise ValueError("jurisdiction, authority, and purpose must not be blank")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")

    def is_active(self, at: datetime | None = None) -> bool:
        moment = at or datetime.now(timezone.utc)
        if moment.tzinfo is None:
            raise ValueError("at must be timezone-aware")
        return self.expires_at is None or moment <= self.expires_at


@dataclass(frozen=True, slots=True)
class ConsentReceipt:
    subject_ref: str
    purposes: frozenset[str]
    issued_at: datetime

    def __post_init__(self) -> None:
        if not self.subject_ref.strip():
            raise ValueError("subject_ref must not be blank")
        if not self.purposes or any(not item.strip() for item in self.purposes):
            raise ValueError("purposes must contain non-empty values")
        if self.issued_at.tzinfo is None:
            raise ValueError("issued_at must be timezone-aware")


def authority_required(action: str, rules: dict[str, bool]) -> bool:
    if not action.strip():
        raise ValueError("action must not be blank")
    return bool(rules.get(action, True))


def evidence_checklist(required: tuple[str, ...], present: set[str]) -> dict[str, bool]:
    if any(not item.strip() for item in required):
        raise ValueError("required checklist items must not be blank")
    return {item: item in present for item in required}


def admissibility_flags(*, integrity_verified: bool, provenance_complete: bool, authorization_verified: bool) -> tuple[str, ...]:
    flags: list[str] = []
    if not integrity_verified:
        flags.append("integrity_not_verified")
    if not provenance_complete:
        flags.append("provenance_incomplete")
    if not authorization_verified:
        flags.append("authorization_not_verified")
    return tuple(flags)
