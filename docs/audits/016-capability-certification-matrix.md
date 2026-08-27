# Audit 016 — Capability Certification Matrix

## Scope

This audit reviews the semantics of the 304-capability registry after the forensic-foundation merges. The goal is to prevent catalog coverage, importability, adapter construction, and live end-to-end certification from being treated as interchangeable claims.

## Finding 1 — Catalog coverage was stronger than a placeholder count, but weaker than certification

`packages/capabilities/coverage.py` contains exactly IDs 1..304 and every entry references importable implementation modules. The existing coverage gate verifies those invariants.

However, `packages/capabilities/tests/test_coverage.py` does not prove that every capability ID is bound to a unique callable or that every referenced third-party system has executed end to end. Module importability is therefore not sufficient evidence for full production certification.

Severity: HIGH for certification semantics; not a code-execution failure.

## Finding 2 — Current audited support split

The registry currently contains:

- 304/304 catalog entries;
- 205 `verified_local` entries;
- 99 `adapter_contract` entries.

`verified_local` means deterministic local behavior is represented by executable implementation code and local test coverage at the implementation-family level.

`adapter_contract` means a concrete command/API contract exists, but the catalog entry must not be represented as live production-certified merely because the adapter can be constructed or imported.

## Finding 3 — Live E2E evidence exists, but cannot safely promote entire capability groups

The repository contains dedicated live E2E suites/workflows for data-foundation services and selected forensic/CTI integrations, including PostgreSQL/PostGIS, Neo4j, OpenSearch, OpenCTI, MISP, Sleuth Kit, Volatility, Velociraptor, and Timesketch.

Those live tests are valuable evidence for the specific adapters they exercise. They do not justify promoting an entire multi-capability group when the current registry maps several capability IDs to broad implementation modules rather than to individual callables/tests.

Therefore this audit deliberately does not bulk-promote the 99 `adapter_contract` entries.

## Correction implemented

Added `packages/capabilities/certification.py` with an explicit certification summary and fail-closed production-certification check.

Added `packages/capabilities/tests/test_certification.py` to enforce the audited 205/99 split and to ensure the repository cannot report full production certification while contract-only capability IDs remain.

The test is automatically executed by the existing `quality` workflow because that workflow discovers the complete `packages/capabilities/tests` suite.

## Remaining certification work

The next promotion pass must be capability-granular. For each of the 99 contract-only IDs, the registry needs evidence that identifies the exact callable/adapter operation, the exact test or workflow that executes it, the third-party version/environment when applicable, and the resulting certification tier.

No capability should be promoted solely because another capability shares the same Python module or external product family.

## Acceptance rule

The project may accurately state "304/304 catalog coverage".

It may not state "304/304 production certified" while `contract_only_capability_ids()` is non-empty.

A future 304/304 production-certification claim is acceptable only when the fail-closed certification gate passes without weakening its semantics.
