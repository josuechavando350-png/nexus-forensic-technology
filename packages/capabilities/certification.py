from __future__ import annotations

from dataclasses import dataclass

from .coverage import CAPABILITY_COVERAGE, TOTAL_CATALOG_CAPABILITIES


@dataclass(frozen=True, slots=True)
class CatalogCertificationSummary:
    total: int
    verified_local: int
    adapter_contract: int

    @property
    def catalog_covered(self) -> bool:
        return self.total == TOTAL_CATALOG_CAPABILITIES

    @property
    def fully_production_certified(self) -> bool:
        """True only when no capability remains at contract-only support."""
        return self.catalog_covered and self.adapter_contract == 0


# Snapshot audited on 2026-08-27. Capability #131 was demoted from
# verified_local to adapter_contract after recovering its authoritative
# blockchain-transaction requirement from the supplied NEXUS source material.
# Any further change to these counts must be accompanied by evidence that
# justifies promotion/demotion of the affected capability IDs.
AUDITED_SUPPORT_BASELINE = {
    "verified_local": 204,
    "adapter_contract": 100,
}


def catalog_certification_summary() -> CatalogCertificationSummary:
    counts = {"verified_local": 0, "adapter_contract": 0}
    for coverage in CAPABILITY_COVERAGE.values():
        counts[coverage.support_level] += 1
    return CatalogCertificationSummary(
        total=len(CAPABILITY_COVERAGE),
        verified_local=counts["verified_local"],
        adapter_contract=counts["adapter_contract"],
    )


def contract_only_capability_ids() -> tuple[int, ...]:
    return tuple(
        capability_id
        for capability_id, coverage in CAPABILITY_COVERAGE.items()
        if coverage.support_level == "adapter_contract"
    )


def require_full_production_certification() -> None:
    """Fail closed instead of allowing 304/304 catalog coverage to imply certification."""
    summary = catalog_certification_summary()
    if not summary.fully_production_certified:
        pending = contract_only_capability_ids()
        raise RuntimeError(
            "full production certification is not satisfied: "
            f"{summary.verified_local} verified_local, "
            f"{summary.adapter_contract} adapter_contract; "
            f"pending capability IDs={pending}"
        )
