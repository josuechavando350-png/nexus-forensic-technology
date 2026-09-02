# Audit 017 — Canonical Capability Specification Matrix

## Objective

Create a fail-closed source of truth for certifying the 304 roadmap capabilities individually. The existing registry proves that every ID from 1 through 304 maps to importable implementation modules and an audited support level. It does not by itself preserve the authoritative requirement text for each ID or map test evidence to each ID individually.

## Finding

At the start of this audit the repository contained no authoritative, complete `ID -> name -> behavior -> acceptance criteria` catalog for capabilities 1..304. User-supplied NEXUS source PDFs recovered during this audit provide explicit numbered definitions for a subset of the roadmap. Those definitions are specification provenance, not automatic implementation evidence.

Technology/company analogy, installation commands, historical snippets, and module-family tests are insufficient on their own to certify a numbered capability.

## Recovered source set

The current recovery pass uses these supplied documents:

- `NEXUS_Componentes_Avanzados_Core.pdf`;
- `NEXUS_codigos_produccion.pdf`;
- `NEXUS_Mapeo_Tecnico_e_Instalacion.pdf` as architecture/mapping support;
- `NEXUS_Tecnologias_Elite_Codigo.pdf` as architecture/behavioral support;
- `NEXUS_Modulos_SIGINT_Identidad.pdf` as implementation-intent support;
- `NEXUS_API_and_Infrastructure_Deployment.pdf` as deployment-intent support;
- `NEXUS_Empresas_Elite_Investigacion.pdf` as conceptual/vendor context only.

Only a source that explicitly binds a roadmap number to a named behavior can create a canonical numbered specification.

## Recovered numbered specifications

This pass currently recovers 12 explicit definitions:

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
- `#295` — Least Privilege;
- `#298` — Tamper-Evident Logging.

`#297 Secrets Management` is explicitly named in the source material but is not promoted to a complete canonical specification in this pass because the same historical snippet embeds the JWT signing key in source. That material establishes historical intent but is not a sound basis for production acceptance criteria.

## Corrected registry claim: capability #131

The recovered source defines `#131` as blockchain transaction/wallet tracing. The prior registry placed `#131` in the local graph-analysis family and marked it `verified_local`. That mapping was not justified by the recovered requirement.

Audit 017 therefore moves `#131` to `packages.integrations.blockchain` and demotes it to `adapter_contract`. The audited support baseline changes from `205 verified_local / 99 adapter_contract` to `204 verified_local / 100 adapter_contract`. A dedicated certification test pins this correction so it cannot silently regress to a local graph claim.

## Prototype and unsafe-source handling

Historical snippets are not promoted to evidence automatically. The supplied `tasks.py` example explicitly states that it simulates heavy intelligence work, sleeps for three seconds, and returns fabricated fixed values such as `entidades_asociadas: 4` and `dictamen_listo: True`. It is useful for recovering the intended meaning of `#219` and `#224`, but it is disqualified as production-certification evidence.

Historical snippets containing embedded credentials/secrets or known method-name defects remain provenance only. Current repository code and tests must independently satisfy recovered acceptance criteria before evidence is attached.

## Individual evidence recovered

`#253` and `#298` now have dedicated executable evidence in `packages/capabilities/tests/test_recovered_audit_log.py`:

- the `#253` test creates a real temporary audit log, verifies the zero-hash genesis record, verifies predecessor-hash linkage across multiple events, and requires the complete chain to validate;
- the `#298` test modifies a persisted audit record after creation and requires integrity verification to fail.

These tests exercise the current `AuditoriaInmutable` implementation, not the historical PDF snippet.

## Current baseline

The current fail-closed matrix is:

- catalog rows: 304;
- canonical specifications recovered: 12;
- canonical specifications missing: 292;
- per-capability evidence mappings: 2;
- per-capability evidence mappings missing: 302;
- support levels: 204 `verified_local`, 100 `adapter_contract`.

These counts do not imply that only two capabilities have functional code. They mean that only two recovered numbered requirements have so far completed the stricter one-to-one requirement-to-test evidence path.

## Fail-closed rule

`require_canonical_specification_complete()` raises until every ID has both an authoritative specification with acceptance criteria and evidence mapped specifically to that capability. Therefore a green quality workflow cannot be interpreted as full 304-capability production certification.

## Promotion procedure

For each capability:

1. recover the authoritative requirement and record its source;
2. define objective acceptance criteria without strengthening the original claim;
3. identify the exact callable or external adapter implementing it;
4. add or identify tests whose assertions prove those criteria;
5. attach live E2E evidence when the claim depends on a third-party runtime, service, hardware device, or network integration;
6. only then attach the per-capability evidence reference and consider certification promotion.

## Next audit pass

Work continues in parallel on two fronts: mine the supplied PDFs for every remaining explicit numbered definition, and audit the current repository against the 12 recovered specifications. Capabilities whose implementation does not meet the recovered requirement are corrected or demoted rather than receiving synthetic evidence.
