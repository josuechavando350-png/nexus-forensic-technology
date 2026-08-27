from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Final, TypedDict

MAX_EVENTS_PER_STREAM: Final[int] = 10_000
MATCH_WINDOW_SECONDS: Final[float] = 5.0


class SensorEvent(TypedDict):
    timestamp_utc: float


def _extract_timestamp(event: Mapping[str, object]) -> float:
    if "timestamp_utc" not in event:
        raise ValueError("sensor event is missing timestamp_utc")
    raw = event["timestamp_utc"]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise TypeError("timestamp_utc must be numeric")
    timestamp = float(raw)
    if not math.isfinite(timestamp):
        raise ValueError("timestamp_utc must be finite")
    return timestamp


def fusionar_sensores_inteligencia(
    senales_satelite: Sequence[Mapping[str, object]],
    trazas_red: Sequence[Mapping[str, object]],
) -> float:
    """Correlaciona dos flujos por proximidad temporal y devuelve 0..100.

    Este valor es una puntuación analítica de coincidencia temporal, no una
    probabilidad de identidad, culpabilidad o pertenencia a una organización.
    """

    if len(senales_satelite) > MAX_EVENTS_PER_STREAM:
        raise ValueError("senales_satelite exceeds the configured event limit")
    if len(trazas_red) > MAX_EVENTS_PER_STREAM:
        raise ValueError("trazas_red exceeds the configured event limit")
    if not senales_satelite or not trazas_red:
        return 0.0

    satellite_times = sorted(_extract_timestamp(event) for event in senales_satelite)
    network_times = sorted(_extract_timestamp(event) for event in trazas_red)

    total_weight = 0.0
    start = 0
    end = 0
    network_count = len(network_times)

    for sat_time in satellite_times:
        lower = sat_time - MATCH_WINDOW_SECONDS
        upper = sat_time + MATCH_WINDOW_SECONDS

        while start < network_count and network_times[start] <= lower:
            start += 1
        if end < start:
            end = start
        while end < network_count and network_times[end] < upper:
            end += 1

        best_weight = 0.0
        for index in range(start, end):
            delta_t = abs(sat_time - network_times[index])
            if delta_t < MATCH_WINDOW_SECONDS:
                best_weight = max(best_weight, math.exp(-delta_t))
        total_weight += best_weight

    normalized = min(1.0, total_weight / float(len(satellite_times)))
    return round(normalized * 100.0, 2)
