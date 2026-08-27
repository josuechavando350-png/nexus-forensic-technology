# Audit 017 — Canonical Capability Specification Matrix

## Objective

Create a fail-closed source of truth for certifying the 304 roadmap capabilities individually. The existing registry proves that every ID from 1 through 304 maps to importable implementation modules and an audited support level. It does not by itself preserve the authoritative requirement text for each ID or map test evidence to each ID individually.

## Finding

At the start of this audit the repository contained no authoritative, complete `ID -> name -> behavior -> acceptance criteria` catalog for capabilities 1..304. The available repository audits described implementation families and certification boundaries, while `packages/capabilities/coverage.py` stored only IDs, implementation-module references, and `verified_local` / `adapter_contract` support levels.

User-supplied NEXUS source PDFs recovered during this audit provide explicit numbered definitions for a subset of the roadmap. Those definitions are now admissible as specification provenance. The PDFs remain distinct from executable implementation evidence: historical code, prototype snippets, installation commands, and vendor/technology mappings do not certify the current repository merely because they describe the intended architecture.

## Recovered source set

The current recovery pass uses these supplied documents as primary specification evidence:

- `NEXUS_Componentes_Avanzados_Core.pdf`;
- `NEXUS_codigos_produccion.pdf`;
- `NEXUS_Mapeo_Tecnico_e_Instalacion.pdf` as architecture/mapping support;
- `NEXUS_Tecnologias_Elite_Codigo.pdf` as architecture/behavioral support;
- `NEXUS_Modulos_SIGINT_Identidad.pdf` as implementation-intent support;
- `NEXUS_API_and_Infrastructure_Deployment.pdf` as deployment-intent support;
- `NEXUS_Empresas_Elite_Investigacion.pdf` as conceptual/vendor context only.

Only documents that explicitly bind a roadmap number to a named behavior may create a canonical numbered row. Technology or company analogy alone is never enough to infer a missing capability number.

## Recovered numbered specifications

This pass recovers 11 capability definitions with explicit source bindings:

- `#104` — Atribución Táctica e Identificación Real;
- `#131` — Rastreo de Billetera Cripto;
- `#134` — Detección de Cuentas Puente o Mula;
- `#181` — Estilometría;
- `#185` — Análisis de Guiones de Engaño NLP;
- `#219` — Complex Event Processing;
- `#224` — Large-Scale Data Processing;
- `#247` — Cadena de Custodia;
- `#253` — Immutable Audit Log;
- `#262` — Generador Automatizado de Dictamen Pericial;
- `#298` — Tamper-Evident Logging.

Acceptance criteria are constrained to behavior actually stated or directly operationalized by the supplied source. They do not strengthen vendor-style marketing claims into legal, attribution, intelligence, or production guarantees.

## Prototype and unsafe-source handling

Historical snippets are not promoted to evidence automatically. One supplied `tasks.py` example explicitly says that it simulates heavy intelligence work, sleeps for three seconds, and returns fabricated fixed values such as `entidades_asociadas: 4` and `dictamen_listo: True`. That material is useful for recovering the intended meaning of `#219` and `#224`, but it is explicitly disqualified as production-certification evidence.

Likewise, historical snippets containing embedded credentials/secrets or known method-name defects remain provenance only. Current repository code and tests must independently satisfy the recovered acceptance criteria before any evidence reference is attached.

## Implementation

`packages/capabilities/specification.py` builds exactly 304 canonical audit rows from the existing registry. Each row carries:

- capability ID;
- authoritative title, when recovered;
- authoritative behavioral description, when recovered;
- explicit acceptance criteria, when recovered;
- current implementation-module references;
- current support level;
- per-capability evidence references, when independently validated;
- authoritative specification source, when available.

A capability is not considered specified merely because its implementation module exists. A capability is not considered individually evidenced merely because some test exercises the same module.

## Current baseline

After the supplied-document recovery pass, the authoritative-source baseline is:

- catalog rows: 304;
- canonical specifications recovered: 11;
- canonical specifications missing: 293;
- per-capability evidence mappings: 0;
- per-capability evidence mappings missing: 304.

These values do **not** state that the repository has zero functional code or zero tests. They state that executable evidence has not yet been attached one-to-one to the recovered capability requirements under the stricter certification rule.

## Fail-closed rule

`require_canonical_specification_complete()` raises until both conditions hold for every ID:

1. an authoritative specification with acceptance criteria is present; and
2. evidence is mapped specifically to that capability.

The normal quality suite tests this fail-closed behavior and pins the current debt baseline. Therefore a green quality workflow cannot be interpreted as full 304-capability production certification.

## Promotion procedure

For each capability, promotion follows this order:

1. recover the authoritative requirement text and record its source;
2. define objective acceptance criteria without strengthening the original claim;
3. identify the exact callable or external adapter implementing that requirement;
4. add or identify tests whose assertions prove those acceptance criteria;
5. attach live E2E evidence when the claim depends on a third-party runtime, service, hardware device, or network integration;
6. only then attach a per-capability evidence reference and consider certification promotion.

Broad module-level or workflow-level success is supporting evidence but is insufficient by itself to promote unrelated capability IDs.

## Next audit pass

The next pass has two tracks in parallel:

1. continue mining the supplied PDFs for additional explicit numbered capability definitions; and
2. for the 11 recovered definitions, audit the current repository implementation and tests against each acceptance criterion, adding evidence only where the match is exact.

Any source that is only conceptual, simulated, vendor-analogous, unsafe, or incomplete stays outside the certification evidence set.
