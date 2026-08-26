from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from .specs import CommandSpec, RequestSpec, require_nonblank


def public_web_request(url: str) -> RequestSpec:
    parsed = urlparse(require_nonblank(url, "url"))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be a public HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError("credential-bearing URLs are not allowed")
    return RequestSpec("GET", url, (("User-Agent", "NEXUS-Forensic/1.0"), ("Accept", "text/html,application/xhtml+xml")))


def dig_dns_command(name: str, record_type: str = "A") -> CommandSpec:
    domain = require_nonblank(name, "name")
    if any(ch.isspace() for ch in domain):
        raise ValueError("name must not contain whitespace")
    rtype = require_nonblank(record_type, "record_type").upper()
    if rtype not in {"A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"}:
        raise ValueError("unsupported DNS record type")
    return CommandSpec(("dig", "+json", domain, rtype))


@dataclass(frozen=True, slots=True)
class NmapHostRecord:
    address: str
    state: str
    services: tuple[tuple[int, str], ...]


def parse_nmap_xml(xml_text: str) -> tuple[NmapHostRecord, ...]:
    root = ET.fromstring(xml_text)
    records: list[NmapHostRecord] = []
    for host in root.findall("host"):
        state_node = host.find("status")
        address_node = host.find("address")
        if state_node is None or address_node is None:
            continue
        address = address_node.attrib.get("addr", "")
        try:
            ip_address(address)
        except ValueError:
            continue
        services: list[tuple[int, str]] = []
        for port in host.findall("./ports/port"):
            try:
                port_id = int(port.attrib["portid"])
            except (KeyError, ValueError):
                continue
            service = port.find("service")
            services.append((port_id, "" if service is None else service.attrib.get("name", "")))
        records.append(NmapHostRecord(address, state_node.attrib.get("state", ""), tuple(sorted(services))))
    return tuple(records)
