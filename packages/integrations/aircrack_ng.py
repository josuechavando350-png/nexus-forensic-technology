from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_MAX_CAPTURE_EXPORT_BYTES = 16 * 1024 * 1024
_MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_NOT_ASSOCIATED = "(not associated)"


class AirodumpParseError(ValueError):
    """Raised when an airodump-ng CSV export is structurally invalid."""


@dataclass(frozen=True, slots=True)
class AirodumpAccessPoint:
    bssid: str
    first_seen: str
    last_seen: str
    channel: int
    speed_mbps: int
    privacy: str
    cipher: str
    authentication: str
    power_dbm: int
    beacons: int
    iv_count: int
    lan_ip: str
    essid: str
    key: str


@dataclass(frozen=True, slots=True)
class AirodumpStation:
    station_mac: str
    first_seen: str
    last_seen: str
    power_dbm: int
    packets: int
    bssid: str | None
    probed_essids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AirodumpSnapshot:
    access_points: tuple[AirodumpAccessPoint, ...]
    stations: tuple[AirodumpStation, ...]


def _clean(value: str) -> str:
    return value.strip()


def _parse_mac(value: str, *, field: str, line_number: int) -> str:
    candidate = _clean(value).upper()
    if not _MAC_RE.fullmatch(candidate):
        raise AirodumpParseError(f"line {line_number}: invalid {field}")
    return candidate


def _parse_int(value: str, *, field: str, line_number: int) -> int:
    candidate = _clean(value)
    try:
        return int(candidate)
    except ValueError as exc:
        raise AirodumpParseError(f"line {line_number}: invalid {field}") from exc


def _parse_access_point(row: list[str], line_number: int) -> AirodumpAccessPoint:
    if len(row) < 15:
        raise AirodumpParseError(f"line {line_number}: truncated access-point row")
    essid = ",".join(row[13:-1]).strip() if len(row) > 15 else _clean(row[13])
    key = _clean(row[-1])
    return AirodumpAccessPoint(
        bssid=_parse_mac(row[0], field="BSSID", line_number=line_number),
        first_seen=_clean(row[1]),
        last_seen=_clean(row[2]),
        channel=_parse_int(row[3], field="channel", line_number=line_number),
        speed_mbps=_parse_int(row[4], field="speed", line_number=line_number),
        privacy=_clean(row[5]),
        cipher=_clean(row[6]),
        authentication=_clean(row[7]),
        power_dbm=_parse_int(row[8], field="power", line_number=line_number),
        beacons=_parse_int(row[9], field="beacons", line_number=line_number),
        iv_count=_parse_int(row[10], field="IV count", line_number=line_number),
        lan_ip=_clean(row[11]),
        essid=essid,
        key=key,
    )


def _parse_station(row: list[str], line_number: int) -> AirodumpStation:
    if len(row) < 7:
        raise AirodumpParseError(f"line {line_number}: truncated station row")
    bssid_raw = _clean(row[5])
    bssid = None if bssid_raw.lower() == _NOT_ASSOCIATED else _parse_mac(
        bssid_raw, field="station BSSID", line_number=line_number
    )
    probes = tuple(item.strip() for item in row[6:] if item.strip())
    return AirodumpStation(
        station_mac=_parse_mac(row[0], field="station MAC", line_number=line_number),
        first_seen=_clean(row[1]),
        last_seen=_clean(row[2]),
        power_dbm=_parse_int(row[3], field="power", line_number=line_number),
        packets=_parse_int(row[4], field="packet count", line_number=line_number),
        bssid=bssid,
        probed_essids=probes,
    )


def parse_airodump_csv(text: str) -> AirodumpSnapshot:
    """Parse an airodump-ng CSV export without executing or controlling radios.

    The parser is intentionally read-only. It accepts the two standard sections
    emitted by airodump-ng (access points followed by stations) and rejects
    malformed evidence instead of silently coercing it.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if len(text.encode("utf-8", errors="surrogatepass")) > _MAX_CAPTURE_EXPORT_BYTES:
        raise AirodumpParseError("airodump-ng export exceeds 16 MiB")

    access_points: list[AirodumpAccessPoint] = []
    stations: list[AirodumpStation] = []
    section: str | None = None

    for line_number, row in enumerate(csv.reader(text.splitlines()), start=1):
        if not row or all(not item.strip() for item in row):
            continue
        first = _clean(row[0]).lstrip("\ufeff")
        if first == "BSSID":
            section = "access_points"
            continue
        if first == "Station MAC":
            section = "stations"
            continue
        if section is None:
            raise AirodumpParseError(f"line {line_number}: data before a recognized header")
        if section == "access_points":
            access_points.append(_parse_access_point(row, line_number))
        else:
            stations.append(_parse_station(row, line_number))

    if section is None:
        raise AirodumpParseError("no airodump-ng CSV headers found")
    return AirodumpSnapshot(tuple(access_points), tuple(stations))


def load_airodump_csv(path: str | Path) -> AirodumpSnapshot:
    """Load and parse a bounded airodump-ng CSV export from local evidence."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    size = source.stat().st_size
    if size > _MAX_CAPTURE_EXPORT_BYTES:
        raise AirodumpParseError("airodump-ng export exceeds 16 MiB")
    raw = source.read_bytes()
    text = raw.decode("utf-8-sig", errors="surrogateescape")
    return parse_airodump_csv(text)
