from __future__ import annotations

from dataclasses import dataclass

TOTAL_CATALOG_CAPABILITIES = 304


@dataclass(frozen=True, slots=True)
class CapabilityCoverage:
    capability_id: int
    implementation_refs: tuple[str, ...]
    support_level: str

    def __post_init__(self) -> None:
        if not 1 <= self.capability_id <= TOTAL_CATALOG_CAPABILITIES:
            raise ValueError("capability_id out of range")
        if not self.implementation_refs:
            raise ValueError("implementation_refs must not be empty")
        if self.support_level not in {"verified_local", "adapter_contract"}:
            raise ValueError("unsupported support_level")


_GROUPS: tuple[tuple[set[int], tuple[str, ...], str], ...] = (
    ({1, 44, 64, 122, 187, 188, 189, 190, 192, 194, 195, 197, 198}, ("packages.forensic_core.geospatial", "packages.integrations.geospatial"), "verified_local"),
    ({2, 38, 39, 65, 67, 116, 124, 208, 209, 225, 226, 227, 228, 229, 234, 237, 243}, ("packages.forensic_core.hypothesis",), "verified_local"),
    ({9, 30, 35, 62, 111, 112, 114, 130, 131, 135, 136, 171, 172, 186, 199, 200, 201, 205, 207, 220, 235, 239, 245, 285, 300}, ("packages.forensic_core.graph", "packages.integrations.graph"), "verified_local"),
    ({12, 47, 160}, ("packages.integrations.cti",), "adapter_contract"),
    ({19, 75}, ("packages.integrations.forensics_cli",), "adapter_contract"),
    ({21, 99, 100, 101, 244, 246, 247, 248, 249, 252, 253, 256, 259, 260, 283, 284, 288, 289, 290, 298, 303, 304}, ("packages.forensic_core.acquisition", "packages.forensic_core.merkle", "packages.forensic_core.packaging", "packages.forensic_core.provenance", "packages.forensic_core.reporting"), "verified_local"),
    ({23, 24, 59, 60, 97, 137}, ("packages.integrations.blockchain",), "adapter_contract"),
    ({37, 63, 94, 121}, ("packages.forensic_core.timeline",), "verified_local"),
    ({46, 58, 98, 127, 128, 129, 144}, ("packages.forensic_core.financial", "packages.forensic_core.anomaly"), "verified_local"),
    ({53, 147, 148, 151, 154}, ("packages.forensic_core.indicators", "packages.integrations.passive_infra"), "adapter_contract"),
    ({66, 232, 233}, ("packages.forensic_core.collection",), "verified_local"),
    ({76, 78, 92, 93}, ("packages.integrations.local_artifacts", "packages.integrations.forensics_cli"), "verified_local"),
    ({83, 223}, ("packages.forensic_core.search", "packages.integrations.search"), "verified_local"),
    ({96}, ("packages.forensic_core.correlation",), "verified_local"),
    ({103, 104, 106, 107, 108, 109, 110, 176, 238, 287}, ("packages.forensic_core.identity",), "verified_local"),
    ({177, 210, 211, 212, 213, 214, 240, 286, 301}, ("packages.forensic_core.anomaly", "packages.integrations.ml"), "verified_local"),
    ({218, 224, 236}, ("packages.integrations.streaming",), "adapter_contract"),
    ({268, 269, 270, 271, 274, 275, 277, 278, 279, 282, 294, 295, 299}, ("packages.forensic_core.policy", "packages.forensic_core.privacy", "packages.integrations.opa"), "verified_local"),
    ({261, 262}, ("packages.forensic_core.reporting",), "verified_local"),
    ({242}, ("packages.forensic_core.case_store",), "verified_local"),
    ({3, 27, 28, 29, 34, 40, 61}, ("packages.forensic_core.case_store", "packages.integrations.platforms", "packages.integrations.search"), "adapter_contract"),
    ({4, 7, 10, 11, 16, 68, 219, 221}, ("packages.forensic_core.streaming", "packages.integrations.streaming"), "adapter_contract"),
    ({5, 13, 26, 31, 32, 36, 120, 123, 125, 126, 230}, ("packages.forensic_core.anomaly", "packages.forensic_core.hypothesis", "packages.forensic_core.identity"), "verified_local"),
    ({6, 8, 15, 17, 18, 20, 25, 55, 56, 69, 70, 71, 72, 73, 74, 77, 79, 80, 81, 82, 84, 85, 86, 87, 88, 89, 90, 91, 95, 102, 163, 164, 165, 168, 293}, ("packages.integrations.defensive_cli",), "adapter_contract"),
    ({14, 291, 292}, ("packages.forensic_core.simulation",), "verified_local"),
    ({22, 113, 115, 117, 118, 119, 153, 166, 173, 174, 202, 203, 204, 206}, ("packages.forensic_core.advanced_graph", "packages.forensic_core.graph", "packages.integrations.cti", "packages.integrations.graph"), "verified_local"),
    ({33, 178, 179, 180, 181, 182, 183, 184, 185, 215, 216, 217, 222, 231}, ("packages.forensic_core.nlp", "packages.integrations.platforms"), "verified_local"),
    ({41, 42, 43, 48, 51, 52, 54, 145, 146, 149, 150, 152, 155, 156, 157, 158, 159, 167}, ("packages.integrations.web_intel", "packages.integrations.passive_infra", "packages.integrations.platforms"), "adapter_contract"),
    ({45, 191, 193, 196}, ("packages.forensic_core.geospatial", "packages.integrations.geospatial", "packages.integrations.forensics_cli"), "verified_local"),
    ({49, 50, 57, 169, 170, 175}, ("packages.forensic_core.identity", "packages.forensic_core.advanced_graph", "packages.integrations.platforms"), "verified_local"),
    ({105}, ("packages.integrations.auth",), "adapter_contract"),
    ({132, 133, 134, 138, 139, 140, 141, 142, 143}, ("packages.forensic_core.financial", "packages.forensic_core.graph", "packages.forensic_core.anomaly", "packages.integrations.blockchain"), "verified_local"),
    ({161, 162}, ("packages.integrations.cti",), "adapter_contract"),
    ({241}, ("packages.forensic_core.case_store", "packages.integrations.crypto_ops"), "verified_local"),
    ({250, 251, 255, 258}, ("packages.integrations.crypto_ops", "packages.forensic_core.security"), "adapter_contract"),
    ({254, 257, 296, 297, 302}, ("packages.forensic_core.security", "packages.integrations.security_services"), "adapter_contract"),
    ({263, 264, 265, 266, 267, 272, 273, 276, 280, 281}, ("packages.forensic_core.legal", "packages.forensic_core.search", "packages.forensic_core.policy"), "verified_local"),
)


def _build_coverage() -> dict[int, CapabilityCoverage]:
    result: dict[int, CapabilityCoverage] = {}
    for capability_ids, refs, level in _GROUPS:
        for capability_id in sorted(capability_ids):
            if capability_id in result:
                raise RuntimeError(f"duplicate capability coverage: {capability_id}")
            result[capability_id] = CapabilityCoverage(capability_id, refs, level)
    return dict(sorted(result.items()))


CAPABILITY_COVERAGE = _build_coverage()


def implemented_capability_count() -> int:
    return len(CAPABILITY_COVERAGE)


def catalog_progress_percent() -> float:
    return implemented_capability_count() * 100.0 / TOTAL_CATALOG_CAPABILITIES
