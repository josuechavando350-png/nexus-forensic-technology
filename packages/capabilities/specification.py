from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from packages.capabilities.coverage import CAPABILITY_COVERAGE, TOTAL_CATALOG_CAPABILITIES


@dataclass(frozen=True, slots=True)
class CapabilitySpecification:
    """Canonical audit row for one roadmap capability.

    A registry/module association is not a specification.  A capability becomes
    specified only when its authoritative name, behavior, acceptance criteria,
    and source are recorded explicitly.  Evidence is tracked per capability so
    module-level tests cannot silently certify unrelated IDs.
    """

    capability_id: int
    title: str | None
    description: str | None
    acceptance_criteria: tuple[str, ...]
    implementation_refs: tuple[str, ...]
    support_level: str
    evidence_refs: tuple[str, ...]
    specification_source: str | None

    @property
    def is_specified(self) -> bool:
        return bool(
            self.title
            and self.title.strip()
            and self.description
            and self.description.strip()
            and self.acceptance_criteria
            and all(item.strip() for item in self.acceptance_criteria)
            and self.specification_source
            and self.specification_source.strip()
        )

    @property
    def has_per_capability_evidence(self) -> bool:
        return bool(self.evidence_refs and all(ref.strip() for ref in self.evidence_refs))


# This mapping is intentionally empty until an authoritative 1..304 roadmap
# source is recovered.  Do not infer names or acceptance criteria from module
# names: doing so would manufacture requirements and recreate the false-green
# condition this audit is designed to eliminate.
_DEFINED_SPECS: Mapping[int, tuple[str, str, tuple[str, ...], tuple[str, ...], str]] = {}


def _build_specifications() -> dict[int, CapabilitySpecification]:
    rows: dict[int, CapabilitySpecification] = {}
    for capability_id, coverage in CAPABILITY_COVERAGE.items():
        defined = _DEFINED_SPECS.get(capability_id)
        if defined is None:
            title = None
            description = None
            acceptance_criteria: tuple[str, ...] = ()
            evidence_refs: tuple[str, ...] = ()
            source = None
        else:
            title, description, acceptance_criteria, evidence_refs, source = defined

        rows[capability_id] = CapabilitySpecification(
            capability_id=capability_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            implementation_refs=coverage.implementation_refs,
            support_level=coverage.support_level,
            evidence_refs=evidence_refs,
            specification_source=source,
        )

    if set(rows) != set(range(1, TOTAL_CATALOG_CAPABILITIES + 1)):
        raise RuntimeError("canonical specification matrix must contain exactly IDs 1..304")
    return rows


CAPABILITY_SPECIFICATIONS = _build_specifications()


def missing_specification_ids() -> tuple[int, ...]:
    return tuple(
        capability_id
        for capability_id, row in CAPABILITY_SPECIFICATIONS.items()
        if not row.is_specified
    )


def missing_per_capability_evidence_ids() -> tuple[int, ...]:
    return tuple(
        capability_id
        for capability_id, row in CAPABILITY_SPECIFICATIONS.items()
        if not row.has_per_capability_evidence
    )


def canonical_audit_summary() -> dict[str, int]:
    specified = TOTAL_CATALOG_CAPABILITIES - len(missing_specification_ids())
    evidenced = TOTAL_CATALOG_CAPABILITIES - len(missing_per_capability_evidence_ids())
    return {
        "catalog_total": TOTAL_CATALOG_CAPABILITIES,
        "specified": specified,
        "spec_missing": TOTAL_CATALOG_CAPABILITIES - specified,
        "per_capability_evidenced": evidenced,
        "per_capability_evidence_missing": TOTAL_CATALOG_CAPABILITIES - evidenced,
    }


def require_canonical_specification_complete() -> None:
    missing_specs = missing_specification_ids()
    missing_evidence = missing_per_capability_evidence_ids()
    if missing_specs or missing_evidence:
        raise RuntimeError(
            "full capability certification is blocked: "
            f"{len(missing_specs)} capability specifications missing; "
            f"{len(missing_evidence)} per-capability evidence mappings missing"
        )
