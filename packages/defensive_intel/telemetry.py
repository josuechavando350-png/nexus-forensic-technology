from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Final, Iterable

MAX_MEMORY_DUMP_BYTES: Final[int] = 64 * 1024 * 1024
DEFAULT_SUSPICIOUS_PORTS: Final[frozenset[int]] = frozenset({4444, 5555, 6667, 9001, 31337})
DEFAULT_MEMORY_SIGNATURES: Final[tuple[bytes, ...]] = (
    b"ROP_CHAIN_DETECTED",
    b"EXPLOIT_PAYLOAD",
    b"/bin/sh",
)


@dataclass(frozen=True, slots=True)
class ConnectionObservation:
    remote_ip: str
    remote_port: int

    def __post_init__(self) -> None:
        ip_address(self.remote_ip)
        if not 1 <= self.remote_port <= 65535:
            raise ValueError("remote_port must be between 1 and 65535")


@dataclass(frozen=True, slots=True)
class TelemetryAssessment:
    status_dispositivo: str
    bytes_analizados: int
    indicadores_inyeccion: tuple[str, ...]
    conexiones_sospechosas: tuple[ConnectionObservation, ...]


def _scan_signatures(memory_dump: bytes, signatures: Iterable[bytes]) -> tuple[str, ...]:
    matches: list[str] = []
    for signature in signatures:
        if not signature:
            raise ValueError("memory signatures must not be empty")
        if signature in memory_dump:
            matches.append(signature.decode("utf-8", errors="replace"))
    return tuple(matches)


def auditar_telemetria_kernel(
    volcado_memoria_bytes: bytes,
    conexiones_activas: Iterable[ConnectionObservation],
    *,
    suspicious_ports: frozenset[int] = DEFAULT_SUSPICIOUS_PORTS,
    signatures: tuple[bytes, ...] = DEFAULT_MEMORY_SIGNATURES,
) -> TelemetryAssessment:
    """Perform a bounded defensive triage over supplied memory bytes and network metadata.

    This function does not claim to prove kernel exploitation. It reports deterministic
    indicators found in evidence already supplied to the engine.
    """
    if len(volcado_memoria_bytes) > MAX_MEMORY_DUMP_BYTES:
        raise ValueError(f"memory dump exceeds {MAX_MEMORY_DUMP_BYTES} bytes")
    if any(port < 1 or port > 65535 for port in suspicious_ports):
        raise ValueError("suspicious_ports contains an invalid TCP/UDP port")

    signature_matches = _scan_signatures(volcado_memoria_bytes, signatures)
    suspicious_connections = tuple(
        connection
        for connection in conexiones_activas
        if connection.remote_port in suspicious_ports
    )
    compromised = bool(signature_matches or suspicious_connections)

    return TelemetryAssessment(
        status_dispositivo="SUSPICIOUS" if compromised else "NO_KNOWN_INDICATORS",
        bytes_analizados=len(volcado_memoria_bytes),
        indicadores_inyeccion=signature_matches,
        conexiones_sospechosas=suspicious_connections,
    )
