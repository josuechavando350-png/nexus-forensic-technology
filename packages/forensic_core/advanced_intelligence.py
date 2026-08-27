from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from re import findall
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlparse


class IntelligenceValidationError(ValueError):
    """Raised when evidence or intelligence input is structurally invalid."""


@dataclass(frozen=True, slots=True)
class CrashTelemetryFinding:
    suspicious: bool
    matched_signals: tuple[str, ...]
    score: float


class MobileExploitTelemetryAnalyzer:
    """Defensive analyzer for crash/telemetry traces associated with memory-corruption TTPs.

    This module detects indicators in already-collected telemetry. It does not generate payloads,
    exploit memory corruption, bypass platform security, or deliver files to devices.
    """

    _SIGNALS: tuple[str, ...] = (
        "stack smashing detected",
        "heap-buffer-overflow",
        "use-after-free",
        "segmentation fault",
        "pointer authentication failure",
        "kernel panic",
        "rop",
    )

    def analyze(self, telemetry: str) -> CrashTelemetryFinding:
        normalized = telemetry.casefold().strip()
        if not normalized:
            raise IntelligenceValidationError("telemetry must not be blank")
        matches = tuple(signal for signal in self._SIGNALS if signal in normalized)
        score = min(1.0, len(matches) / 3.0)
        return CrashTelemetryFinding(
            suspicious=len(matches) >= 2,
            matched_signals=matches,
            score=score,
        )


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    source: str
    alias: str | None = None
    email: str | None = None
    phone: str | None = None
    ip: str | None = None


@dataclass(frozen=True, slots=True)
class EntityResolutionResult:
    linked: bool
    confidence: float
    shared_attributes: tuple[str, ...]


class DeterministicEntityResolver:
    """Deterministic entity-resolution engine for lawfully obtained investigation records."""

    _WEIGHTS: Mapping[str, float] = {
        "email": 0.40,
        "phone": 0.35,
        "ip": 0.15,
        "alias": 0.10,
    }

    @staticmethod
    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.casefold().strip()
        return normalized or None

    def compare(self, left: IdentityRecord, right: IdentityRecord) -> EntityResolutionResult:
        shared: list[str] = []
        score = 0.0
        for field, weight in self._WEIGHTS.items():
            left_value = self._normalize(getattr(left, field))
            right_value = self._normalize(getattr(right, field))
            if left_value is not None and left_value == right_value:
                shared.append(field)
                score += weight
        confidence = round(min(1.0, score), 4)
        return EntityResolutionResult(
            linked=confidence >= 0.50,
            confidence=confidence,
            shared_attributes=tuple(shared),
        )


@dataclass(frozen=True, slots=True)
class BehavioralProfile:
    token_count: int
    vocabulary_size: int
    lexical_richness: float
    normalized_vector: Mapping[str, float]


class BehavioralNLPProfiler:
    """Creates a deterministic lexical behavior fingerprint from supplied text evidence."""

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = text.casefold().strip()
        if not normalized:
            raise IntelligenceValidationError("text must not be blank")
        return findall(r"\b[\wáéíóúüñ]+\b", normalized, flags=0)

    def profile(self, text: str) -> BehavioralProfile:
        tokens = self._tokens(text)
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        norm = sqrt(sum(float(value * value) for value in counts.values())) or 1.0
        vector = {token: round(count / norm, 8) for token, count in sorted(counts.items())}
        return BehavioralProfile(
            token_count=len(tokens),
            vocabulary_size=len(counts),
            lexical_richness=round(len(counts) / len(tokens), 8),
            normalized_vector=vector,
        )

    def cosine_similarity(self, left: BehavioralProfile, right: BehavioralProfile) -> float:
        shared = set(left.normalized_vector) & set(right.normalized_vector)
        return round(
            sum(left.normalized_vector[token] * right.normalized_vector[token] for token in shared),
            8,
        )


@dataclass(frozen=True, slots=True)
class ForensicAcquisitionManifest:
    device_id: str
    examiner_id: str
    authorization_reference: str
    image_sha256: str
    byte_length: int


class AuthorizedAcquisitionRegistry:
    """Registers hashes of forensic images acquired through separately authorized tooling.

    The registry intentionally does not contain bootloader exploits, screen-lock bypasses, or
    instructions for defeating device security controls.
    """

    def register(
        self,
        *,
        device_id: str,
        examiner_id: str,
        authorization_reference: str,
        image_bytes: bytes,
    ) -> ForensicAcquisitionManifest:
        if not device_id.strip() or not examiner_id.strip() or not authorization_reference.strip():
            raise IntelligenceValidationError("device, examiner, and authorization are required")
        if not image_bytes:
            raise IntelligenceValidationError("forensic image must not be empty")
        return ForensicAcquisitionManifest(
            device_id=device_id.strip(),
            examiner_id=examiner_id.strip(),
            authorization_reference=authorization_reference.strip(),
            image_sha256=sha256(image_bytes).hexdigest(),
            byte_length=len(image_bytes),
        )


@dataclass(frozen=True, slots=True)
class IOC:
    kind: str
    value: str
    source: str


class PassiveCTIHarvester:
    """Extracts IOCs from supplied/public intelligence text without credential theft or intrusion."""

    def harvest(self, text: str, *, source: str) -> tuple[IOC, ...]:
        if not source.strip():
            raise IntelligenceValidationError("source must not be blank")
        normalized = text.strip()
        if not normalized:
            return ()
        findings: set[tuple[str, str]] = set()
        for email in findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", normalized):
            findings.add(("email", email.casefold()))
        for digest in findall(r"\b[a-fA-F0-9]{64}\b", normalized):
            findings.add(("sha256", digest.casefold()))
        for ipv4 in findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", normalized):
            octets = ipv4.split(".")
            if all(0 <= int(octet) <= 255 for octet in octets):
                findings.add(("ipv4", ipv4))
        return tuple(IOC(kind=kind, value=value, source=source.strip()) for kind, value in sorted(findings))

    @staticmethod
    def validate_research_url(url: str) -> str:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise IntelligenceValidationError("research URL must be an absolute HTTP(S) URL")
        return url.strip()


@dataclass(frozen=True, slots=True)
class OSINTArchiveRecord:
    url: str
    observed_at: str
    content_sha256: str


class PassiveOSINTArchive:
    """Builds provenance records for content already retrieved from lawful/public sources."""

    def record(self, *, url: str, observed_at: str, content: bytes) -> OSINTArchiveRecord:
        if not observed_at.strip():
            raise IntelligenceValidationError("observed_at must not be blank")
        validated_url = PassiveCTIHarvester.validate_research_url(url)
        if not content:
            raise IntelligenceValidationError("archived content must not be empty")
        return OSINTArchiveRecord(
            url=validated_url,
            observed_at=observed_at.strip(),
            content_sha256=sha256(content).hexdigest(),
        )


def stable_identity_fingerprint(records: Sequence[IdentityRecord]) -> str:
    if not records:
        raise IntelligenceValidationError("records must not be empty")
    serialized = "\n".join(
        "|".join(
            (
                record.source.strip(),
                (record.alias or "").casefold().strip(),
                (record.email or "").casefold().strip(),
                (record.phone or "").strip(),
                (record.ip or "").strip(),
            )
        )
        for record in sorted(records, key=lambda item: (item.source, item.email or "", item.phone or ""))
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def deduplicate_iocs(iocs: Iterable[IOC]) -> tuple[IOC, ...]:
    unique = {(item.kind, item.value, item.source): item for item in iocs}
    return tuple(unique[key] for key in sorted(unique))
