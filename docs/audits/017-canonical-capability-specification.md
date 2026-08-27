# Audit 017 — Canonical Capability Specification Matrix

## Objective

Create a fail-closed source of truth for certifying the 304 roadmap capabilities individually. The existing registry proves that every ID from 1 through 304 maps to importable implementation modules and an audited support level. It does not preserve the authoritative requirement text for each ID and it does not map test evidence to each ID individually.

## Finding

At the start of this audit the repository contains no authoritative, complete `ID -> name -> behavior -> acceptance criteria` catalog for capabilities 1..304. The available audit documents describe implementation families and certification boundaries, while `packages/capabilities/coverage.py` stores only IDs, implementation-module references, and `verified_local` / `adapter_contract` support levels.

It would be technically possible to generate names and requirements from module names, but doing so would manufacture requirements. This audit explicitly refuses that approach.

## Implementation

`packages/capabilities/specification.py` now builds exactly 304 canonical audit rows from the existing registry. Each row carries:

- capability ID;
- authoritative title, when available;
- authoritative behavioral description, when available;
- explicit acceptance criteria, when available;
- current implementation-module references;
- current support level;
- per-capability evidence references, when available;
- authoritative specification source, when available.

A capability is not considered specified merely because its implementation module exists. A capability is not considered individually evidenced merely because some test exercises the same module.

## Current baseline

The current authoritative-source baseline is:

- catalog rows: 304;
- canonical specifications recovered: 0;
- canonical specifications missing: 304;
- per-capability evidence mappings: 0;
- per-capability evidence mappings missing: 304.

These values do **not** state that the repository has zero functional code or zero tests. They state that the repository cannot yet prove a one-to-one relationship between each roadmap requirement and its acceptance evidence because the exact roadmap definitions are absent from the repository.

## Fail-closed rule

`require_canonical_specification_complete()` raises until both conditions hold for every ID:

1. an authoritative specification with acceptance criteria is present; and
2. evidence is mapped specifically to that capability.

The normal quality suite tests this fail-closed behavior and pins the current debt baseline. Therefore a green quality workflow cannot be interpreted as full 304-capability production certification.

## Promotion procedure

For each capability, promotion must follow this order:

1. recover the authoritative requirement text and record its source;
2. define objective acceptance criteria without strengthening the original claim;
3. identify the exact callable or external adapter implementing that requirement;
4. add or identify tests whose assertions prove those acceptance criteria;
5. attach live E2E evidence when the claim depends on a third-party runtime, service, hardware device, or network integration;
6. only then update the capability's certification status.

Broad module-level or workflow-level success is supporting evidence but is insufficient by itself to promote unrelated capability IDs.

## Blocking dependency

The next substantive certification step requires recovery of the authoritative original 1..304 roadmap source. Until that source is available, the correct state is `spec_missing`; inventing titles or acceptance criteria would create another false-green registry.
