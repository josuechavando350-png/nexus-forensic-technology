from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import FrozenSet


@dataclass(frozen=True, slots=True)
class AuthorizationScope:
    case_id: str
    purposes: FrozenSet[str]
    source_types: FrozenSet[str]
    actions: FrozenSet[str]
    valid_until: datetime

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be blank")
        if not self.purposes or not self.source_types or not self.actions:
            raise ValueError("purposes, source_types, and actions must not be empty")
        if self.valid_until.tzinfo is None or self.valid_until.utcoffset() is None:
            raise ValueError("valid_until must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: str


def authorize(scope: AuthorizationScope, *, purpose: str, source_type: str, action: str, at: datetime) -> AuthorizationDecision:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("at must be timezone-aware")
    if at.astimezone(timezone.utc) > scope.valid_until.astimezone(timezone.utc):
        return AuthorizationDecision(False, "authorization-expired")
    if purpose not in scope.purposes:
        return AuthorizationDecision(False, "purpose-not-authorized")
    if source_type not in scope.source_types:
        return AuthorizationDecision(False, "source-type-not-authorized")
    if action not in scope.actions:
        return AuthorizationDecision(False, "action-not-authorized")
    return AuthorizationDecision(True, "authorized")
