from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ForensicEvent:
    event_id: str
    occurred_at: datetime
    source_ref: str
    kind: str
    summary: str

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be blank")
        if not self.source_ref.strip():
            raise ValueError("source_ref must not be blank")
        if not self.kind.strip():
            raise ValueError("kind must not be blank")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")


class Timeline:
    def __init__(self, events: Iterable[ForensicEvent] = ()) -> None:
        self._events: dict[str, ForensicEvent] = {}
        for event in events:
            self.add(event)

    def add(self, event: ForensicEvent) -> None:
        if not isinstance(event, ForensicEvent):
            raise TypeError("event must be a ForensicEvent")
        if event.event_id in self._events:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        self._events[event.event_id] = event

    def ordered(self) -> tuple[ForensicEvent, ...]:
        return tuple(sorted(self._events.values(), key=lambda event: (event.occurred_at.astimezone(timezone.utc), event.event_id)))

    def between(self, start: datetime, end: datetime) -> tuple[ForensicEvent, ...]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must be timezone-aware")
        if end < start:
            raise ValueError("end must be greater than or equal to start")
        return tuple(event for event in self.ordered() if start <= event.occurred_at <= end)
