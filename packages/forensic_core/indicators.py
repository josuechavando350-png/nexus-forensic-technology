from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import re
from urllib.parse import urlsplit, urlunsplit


_DOMAIN_RE = re.compile(r"^(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$", re.IGNORECASE)


def normalize_ip(value: str) -> str:
    return ip_address(value.strip()).compressed


def normalize_domain(value: str) -> str:
    candidate = value.strip().rstrip(".").casefold()
    if not _DOMAIN_RE.fullmatch(candidate):
        raise ValueError("invalid domain")
    return candidate.encode("idna").decode("ascii")


def normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme.casefold() not in {"http", "https"}:
        raise ValueError("URL scheme must be http or https")
    if not parts.hostname:
        raise ValueError("URL must contain a hostname")
    host = normalize_domain(parts.hostname)
    port = parts.port
    default_port = (parts.scheme.casefold() == "http" and port == 80) or (parts.scheme.casefold() == "https" and port == 443)
    authority = host if port is None or default_port else f"{host}:{port}"
    path = parts.path or "/"
    return urlunsplit((parts.scheme.casefold(), authority, path, parts.query, ""))


@dataclass(frozen=True, slots=True)
class Indicator:
    kind: str
    value: str

    @classmethod
    def parse(cls, kind: str, value: str) -> "Indicator":
        kind = kind.casefold().strip()
        normalizers = {"ip": normalize_ip, "domain": normalize_domain, "url": normalize_url}
        if kind not in normalizers:
            raise ValueError("unsupported indicator kind")
        return cls(kind, normalizers[kind](value))
