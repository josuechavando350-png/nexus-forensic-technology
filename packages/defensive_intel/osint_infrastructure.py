from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from typing import Any
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class InfrastructureIntel:
    domain: str
    addresses: tuple[str, ...]
    rdap_names: tuple[str, ...]


def _normalize_domain(domain: str) -> str:
    value = domain.strip().lower().rstrip(".")
    if not value or len(value) > 253 or "/" in value or ":" in value:
        raise ValueError("invalid domain name")
    try:
        return value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("invalid internationalized domain name") from exc


def _resolve(domain: str) -> tuple[str, ...]:
    try:
        infos = socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError("public DNS lookup failed") from exc
    values = tuple(sorted({str(info[4][0]) for info in infos}))
    if not values:
        raise RuntimeError("public DNS lookup returned no addresses")
    return values


def _rdap_name(address: str, timeout: float) -> str:
    request = Request(
        f"https://rdap.org/ip/{address}",
        headers={"Accept": "application/rdap+json, application/json", "User-Agent": "NEXUS-Investigation-OS/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"RDAP HTTP status {response.status}")
            payload: Any = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("public RDAP lookup failed") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("RDAP payload must be a JSON object")
    name = payload.get("name")
    return str(name) if name is not None else "UNKNOWN"


def ejecutar_rastreo_infraestructura_pasiva(domain: str, *, timeout: float = 5.0) -> InfrastructureIntel:
    """Collect public DNS and RDAP registration metadata only."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    normalized = _normalize_domain(domain)
    addresses = _resolve(normalized)
    names = tuple(_rdap_name(address, timeout) for address in addresses)
    return InfrastructureIntel(domain=normalized, addresses=addresses, rdap_names=names)
