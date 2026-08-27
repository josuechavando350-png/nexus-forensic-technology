from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from packages.capabilities.coverage import CAPABILITY_COVERAGE, TOTAL_CATALOG_CAPABILITIES


@dataclass(frozen=True, slots=True)
class CapabilitySpecification:
    """Canonical audit row for one roadmap capability.

    A registry/module association is not a specification. A capability becomes
    specified only when its authoritative name, behavior, acceptance criteria,
    and source are recorded explicitly. Evidence is tracked per capability so
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


_DEFINED_SPECS: Mapping[int, tuple[str, str, tuple[str, ...], tuple[str, ...], str]] = {
    104: (
        "Atribución Táctica e Identificación Real",
        "Produce structured attribution fields for a case, including source IP, H3 operating zone, linked telephone, financial account, and identified account holder when those values exist.",
        (
            "Represent source IP, H3 zone, linked telephone, financial account, and identified holder as explicit attribution fields.",
            "Do not treat absent attribution fields as independently verified identity evidence.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §1, heading 'ATRIBUCIÓN TÁCTICA E IDENTIFICACIÓN REAL (#104)'",
    ),
    131: (
        "Rastreo de Billetera Cripto",
        "Reconstructs a blockchain transaction flow from a transaction hash and exposes origin wallet, destination wallet, and transferred value.",
        (
            "Accept a blockchain transaction hash through an explicit provider connection.",
            "Return the transaction hash, origin wallet, destination wallet, and transferred amount when the provider supplies the transaction.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §2, 'rastrear_billetera_cripto' (#131)",
    ),
    134: (
        "Detección de Cuentas Puente o Mula",
        "Detects accounts that rapidly disperse a configured proportion of incoming funds within a configured time window.",
        (
            "Calculate incoming and outgoing totals per account from timestamped transactions.",
            "Flag an account only when the outgoing/incoming ratio meets the configured threshold and the dispersal occurs inside the configured time window.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §2, 'analizar_red_cuentas_mula' (#134)",
    ),
    181: (
        "Estilometría",
        "Extracts a deterministic linguistic profile from text using token counts, average word length, lexical richness, and frequent vocabulary.",
        (
            "Normalize and tokenize the supplied text before measurement.",
            "Return total words, average word length, lexical richness, and frequent vocabulary without asserting real-world identity from those measurements alone.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §3, 'extraer_perfil_estilometrico' (#181)",
    ),
    185: (
        "Análisis de Guiones de Engaño NLP",
        "Scores supplied text against a knowledge base of scam/extortion script keywords and returns the highest-scoring category or an unclassified result.",
        (
            "Count keyword matches for every configured script category.",
            "Return the category with the highest positive score, otherwise return an explicit unclassified result together with the score matrix.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §3, 'clasificar_guion_extorsion' (#185)",
    ),
    219: (
        "Complex Event Processing",
        "Executes heavy intelligence-processing work outside the synchronous web request path through an asynchronous worker contract.",
        (
            "Dispatch heavy processing through an asynchronous worker rather than blocking the API request thread.",
            "Expose a deterministic task result contract instead of relying on console output as completion evidence.",
        ),
        (),
        "NEXUS_codigos_produccion.pdf §2, 'Módulos NEXUS implicados: #219 (Complex Event Processing)'",
    ),
    224: (
        "Large-Scale Data Processing",
        "Provides a background-processing path for high-consumption forensic/intelligence workloads using a queue-backed worker architecture.",
        (
            "Use an explicit broker-backed task queue for background execution.",
            "Treat simulated sleeps or fabricated result counts as prototype behavior, not successful production processing.",
        ),
        (),
        "NEXUS_codigos_produccion.pdf §2, 'Módulos NEXUS implicados: #224 (Large-Scale Data Processing)'",
    ),
    247: (
        "Cadena de Custodia",
        "Preserves evidence integrity metadata in the pericial output by associating each evidence element with its cryptographic hash.",
        (
            "List each preserved evidence element together with its cryptographic integrity value.",
            "Do not represent a missing or unverified integrity value as preserved chain-of-custody evidence.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §1, heading 'ELEMENTOS PROBATORIOS CONSERVADOS (CADENA DE CUSTODIA #247)'",
    ),
    253: (
        "Immutable Audit Log",
        "Maintains an append-only audit sequence in which each record contains the hash of the preceding record and its own SHA-256 integrity value.",
        (
            "Create a genesis record anchored to a zero previous hash.",
            "For every subsequent audit event, persist the previous record hash and calculate a new SHA-256 hash over the record content.",
            "Detect a broken hash chain rather than accepting altered records as valid audit history.",
        ),
        (
            "packages/capabilities/tests/test_recovered_audit_log.py::RecoveredAuditLogCapabilityTests.test_capability_253_immutable_audit_log_chains_records",
        ),
        "NEXUS_codigos_produccion.pdf §1, 'Módulos NEXUS implicados: #253 (Immutable Audit Log)'",
    ),
    262: (
        "Generador Automatizado de Dictamen Pericial",
        "Generates a structured forensic report from case data, including case metadata, preserved evidence hashes, and attributed technical indicators.",
        (
            "Generate a report artifact from an explicit case identifier and case data.",
            "Include preserved evidence and integrity hashes in a dedicated evidence section.",
            "Render attribution fields as reported case data without converting missing inputs into fabricated findings.",
        ),
        (),
        "NEXUS_Componentes_Avanzados_Core.pdf §1, 'Generador Automatizado de Dictamen Pericial (#262)'",
    ),
    295: (
        "Least Privilege",
        "Protects routes through bearer-token validation and explicit authentication claims so protected endpoints reject unauthenticated or invalid callers.",
        (
            "Require a bearer credential before admitting a caller to a protected route.",
            "Reject expired or invalid tokens instead of returning an authenticated context.",
            "Expose authorization claims explicitly; a single hard-coded role is not evidence of complete role-based access control.",
        ),
        (),
        "NEXUS_codigos_produccion.pdf §3, 'Módulos NEXUS implicados: #295 (Least Privilege)'",
    ),
    298: (
        "Tamper-Evident Logging",
        "Makes audit-log modification detectable by cryptographically chaining records with SHA-256 hashes.",
        (
            "Bind every non-genesis audit record to the exact hash of its predecessor.",
            "Verification must fail when a record hash or predecessor link no longer matches the stored chain.",
        ),
        (
            "packages/capabilities/tests/test_recovered_audit_log.py::RecoveredAuditLogCapabilityTests.test_capability_298_tamper_evident_logging_rejects_modified_chain",
        ),
        "NEXUS_codigos_produccion.pdf §1, 'Módulos NEXUS implicados: #298 (Tamper-Evident Logging)'",
    ),
}


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
