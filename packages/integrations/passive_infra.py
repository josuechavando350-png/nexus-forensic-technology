from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Mapping
from urllib.parse import quote


@dataclass(slots=True)
class PassiveInfrastructureAdapter:
    http_client: Any

    def rdap_domain(self, domain: str, *, base_url: str = "https://rdap.org/domain") -> Mapping[str, Any]:
        domain = domain.strip().casefold().rstrip(".")
        if not domain or "/" in domain:
            raise ValueError("invalid domain")
        response = self.http_client.get(f"{base_url.rstrip('/')}/{quote(domain)}", timeout=20.0)
        response.raise_for_status()
        return response.json()

    def rdap_ip(self, address: str, *, base_url: str = "https://rdap.org/ip") -> Mapping[str, Any]:
        normalized = ip_address(address.strip()).compressed
        response = self.http_client.get(f"{base_url.rstrip('/')}/{quote(normalized)}", timeout=20.0)
        response.raise_for_status()
        return response.json()

    def certificate_transparency(self, domain: str, *, base_url: str = "https://crt.sh/") -> list[dict[str, Any]]:
        domain = domain.strip().casefold().rstrip(".")
        if not domain:
            raise ValueError("domain must not be blank")
        response = self.http_client.get(base_url, params={"q": f"%.{domain}", "output": "json"}, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
        return list(payload) if isinstance(payload, list) else []

    @staticmethod
    def parse_bgp_records(records: list[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
        routes: dict[str, set[str]] = {}
        for record in records:
            prefix = str(record.get("prefix", "")).strip()
            origin = str(record.get("origin", "")).strip()
            if not prefix or not origin:
                continue
            routes.setdefault(prefix, set()).add(origin)
        return {prefix: tuple(sorted(origins)) for prefix, origins in sorted(routes.items())}
