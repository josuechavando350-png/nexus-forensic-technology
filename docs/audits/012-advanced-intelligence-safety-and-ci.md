# Audit 012 — Advanced intelligence defensive boundary and CI repair

## Scope

This audit covers `packages/forensic_core/advanced_intelligence.py`, its unit tests, the `config.py` strict-typing repair, and the `api-foundation` workflow extension.

## Requested technology mapping

The user requested five technology families. Only defensive, forensic, or lawfully supplied-data implementations are admitted into NEXUS:

1. Mobile memory-corruption / ROP technology -> `MobileExploitTelemetryAnalyzer` detects memory-corruption indicators in crash telemetry already collected from a device. It does not generate exploits, malformed payloads, ROP chains, kernel escalation, or delivery mechanisms.
2. OSINT / synthetic-identity technology -> `PassiveOSINTArchive` records provenance for content already retrieved from public/lawful sources. No fake-person generation, covert persona operation, credential theft, login automation, or anti-bot evasion is implemented.
3. Gotham-style ontology / entity resolution -> `DeterministicEntityResolver` links records using normalized, explicitly weighted identifiers. `stable_identity_fingerprint` creates deterministic case fingerprints. This is an analytic linkage result, not a claim of real-world identity.
4. Behavioral NLP / forensic acquisition -> `BehavioralNLPProfiler` creates deterministic lexical vectors and cosine similarity. `AuthorizedAcquisitionRegistry` records SHA-256 manifests for images acquired by separately authorized tooling. It does not bypass bootloaders, lock screens, encryption, or hardware security.
5. CTI / dark-web intelligence -> `PassiveCTIHarvester` extracts IOCs from text already supplied to the engine and validates research URLs. It does not infiltrate closed forums, automate Telegram access, steal credentials/tokens, or bypass access controls.

## Code audit

### Input validation

- Blank telemetry and blank NLP text raise `IntelligenceValidationError`.
- Forensic acquisition requires device ID, examiner ID, authorization reference, and non-empty image bytes.
- OSINT provenance requires an absolute HTTP(S) URL, observation time, and non-empty content.
- CTI harvesting accepts supplied text only and validates IPv4 octets before emitting an IOC.

### Determinism

- Identity matching uses fixed weights and normalized values.
- Identity fingerprints sort records before hashing.
- NLP vectors sort vocabulary before materializing the mapping.
- IOC de-duplication sorts the tuple key before returning output.
- All forensic image and archive fingerprints use SHA-256 from Python `hashlib`.

### Safety and evidentiary boundary

- Entity resolution returns `confidence` and shared attributes; it does not label a person guilty or create an unreviewable attribution.
- Mobile analysis is detection-only.
- Acquisition is manifest-only and assumes external lawful acquisition.
- CTI and OSINT modules operate on supplied/public data; no unauthorized collection primitives are present.

## Tests

`packages/forensic_core/tests/test_advanced_intelligence.py` verifies:

- memory-corruption telemetry scoring and blank rejection;
- deterministic entity linking;
- deterministic NLP profiles and identity fingerprints;
- SHA-256 acquisition manifests;
- passive IOC extraction and de-duplication;
- provenance hashing for public archive material.

## CI failure found and repaired

The second `api-foundation` run failed at strict mypy because `BaseSettings` resolves required fields dynamically from environment variables while mypy models the generated constructor as requiring explicit keyword arguments. The runtime code was valid; the static analyzer reported six `call-arg` errors at `settings = Settings()`.

The repair keeps the canonical pydantic-settings runtime initialization and adds the narrowest possible `# type: ignore[call-arg]` on that single dynamic construction site, with an explanatory comment. No global type-check suppression was added.

The workflow now also compiles and type-checks `advanced_intelligence.py` and executes its dedicated test suite.

## Acceptance criteria

This audit passes only when both `quality` and `api-foundation / certify-api-foundation` complete successfully on the new head commit. Until then the PR remains draft and must not be merged.
