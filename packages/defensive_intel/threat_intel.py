from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Literal
from urllib.parse import quote
from urllib.request import Request, urlopen

IndicatorType = Literal["IPv4", "IPv6", "domain", "hostname", "file"]


@dataclass(frozen=True, slots=True)
class ThreatReputation:
    indicator: str
    indicator_type: IndicatorType
    pulse_count: int
    malicious_file_count: int
    provider: str = "AlienVault OTX"

    @property
    def has_known_indicators(self) -> bool:
        return self.pulse_count > 0 or self.malicious_file_count > 0


def verificar_reputacion_amenaza(
    indicador: str,
    tipo: IndicatorType,
    *,
    timeout: float = 5.0,
    api_key: str | None = None,
) -> ThreatReputation:
    """Query the public OTX indicator endpoint for defensive CTI correlation.

    The function reports provider observations only; it does not infer criminal identity,
    intent, or guilt from an indicator match.
    """
    value = indicador.strip()
    if not value or len(value) > 2048:
        raise ValueError("indicator must be non-empty and at most 2048 characters")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    key = api_key if api_key is not None else os.getenv("OTX_API_KEY")
    headers = {"Accept": "application/json", "User-Agent": "NEXUS-Investigation-OS/1.0"}
    if key:
        headers["X-OTX-API-KEY"] = key
    url = f"https://otx.alienvault.com/api/v1/indicators/{tipo}/{quote(value, safe='')}/general"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"OTX returned HTTP {response.status}")
            payload: Any = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("OTX reputation lookup failed") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("OTX response must be a JSON object")
    pulse_info = payload.get("pulse_info")
    pulse_count = 0
    if isinstance(pulse_info, dict):
        count = pulse_info.get("count", 0)
        if isinstance(count, int) and count >= 0:
            pulse_count = count
    validation = payload.get("validation")
    malicious_file_count = 0
    if isinstance(validation, list):
        malicious_file_count = sum(1 for item in validation if isinstance(item, dict) and item.get("source"))
    return ThreatReputation(
        indicator=value,
        indicator_type=tipo,
        pulse_count=pulse_count,
        malicious_file_count=malicious_file_count,
    )
