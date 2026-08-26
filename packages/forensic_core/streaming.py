from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Event:
    timestamp: datetime
    kind: str
    value: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if not self.kind.strip():
            raise ValueError("kind must not be blank")


def weighted_sensor_fusion(samples: tuple[tuple[float, float], ...]) -> float:
    if not samples:
        raise ValueError("samples must not be empty")
    if any(weight < 0 for _, weight in samples):
        raise ValueError("weights must be non-negative")
    total_weight = sum(weight for _, weight in samples)
    if total_weight <= 0:
        raise ValueError("total weight must be positive")
    return sum(value * weight for value, weight in samples) / total_weight


def detect_sequence(events: tuple[Event, ...], kinds: tuple[str, ...]) -> bool:
    if not kinds:
        raise ValueError("kinds must not be empty")
    ordered = sorted(events, key=lambda item: item.timestamp)
    index = 0
    for event in ordered:
        if event.kind == kinds[index]:
            index += 1
            if index == len(kinds):
                return True
    return False
