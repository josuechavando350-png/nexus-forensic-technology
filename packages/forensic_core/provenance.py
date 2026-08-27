from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Iterable, Mapping


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canonical_json(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class CustodyEvent:
    evidence_id: str
    actor: str
    action: str
    timestamp: datetime
    previous_hash: str | None
    event_hash: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be blank")
        if not self.actor.strip():
            raise ValueError("actor must not be blank")
        if not self.action.strip():
            raise ValueError("action must not be blank")
        _require_utc(self.timestamp)
        if self.previous_hash is not None and len(self.previous_hash) != 64:
            raise ValueError("previous_hash must be a SHA-256 hex digest")
        if len(self.event_hash) != 64:
            raise ValueError("event_hash must be a SHA-256 hex digest")


def _event_digest(*, evidence_id: str, actor: str, action: str, timestamp: datetime, previous_hash: str | None) -> str:
    payload = {
        "action": action,
        "actor": actor,
        "evidence_id": evidence_id,
        "previous_hash": previous_hash,
        "timestamp": _require_utc(timestamp).isoformat().replace("+00:00", "Z"),
    }
    return sha256(_canonical_json(payload)).hexdigest()


class ChainOfCustody:
    def __init__(self, events: Iterable[CustodyEvent] = ()) -> None:
        self._events = list(events)
        if not self.verify():
            raise ValueError("invalid custody chain")

    @property
    def events(self) -> tuple[CustodyEvent, ...]:
        return tuple(self._events)

    def append(self, *, evidence_id: str, actor: str, action: str, timestamp: datetime) -> CustodyEvent:
        previous_hash = self._events[-1].event_hash if self._events else None
        digest = _event_digest(evidence_id=evidence_id, actor=actor, action=action, timestamp=timestamp, previous_hash=previous_hash)
        event = CustodyEvent(evidence_id=evidence_id, actor=actor, action=action, timestamp=_require_utc(timestamp), previous_hash=previous_hash, event_hash=digest)
        self._events.append(event)
        return event

    def verify(self) -> bool:
        previous_hash: str | None = None
        for event in self._events:
            if event.previous_hash != previous_hash:
                return False
            expected = _event_digest(evidence_id=event.evidence_id, actor=event.actor, action=event.action, timestamp=event.timestamp, previous_hash=previous_hash)
            if expected != event.event_hash:
                return False
            previous_hash = event.event_hash
        return True
