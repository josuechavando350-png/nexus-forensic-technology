# Audit 006 — Full 304-Capability Catalog Coverage

## Objective

Extend the audited implementation registry from 152/304 to 304/304 without treating documentation, placeholders, TODOs, empty modules, or unverified external services as production-complete implementations.

## Counting rule

Every capability ID from 1 through 304 must exist exactly once in `packages/capabilities/coverage.py`. Each entry must reference importable code and must declare one of two support levels:

- `verified_local`: deterministic local behavior is implemented and covered by executable tests.
- `adapter_contract`: an actual command/API request contract is implemented and tested, while the external runtime or service remains explicitly outside the local CI verification boundary.

The registry test fails if any capability identifier is missing, duplicated, outside the 1..304 range, has no implementation reference, or references a module that cannot be imported.

## New implementation families in the second half

### Defensive/offline forensic tooling

`packages/integrations/defensive_cli.py` adds shell-free argv contracts for YARA, Volatility 3, Zeek offline PCAP analysis, tshark offline PCAP analysis, osquery read-only SELECT queries, Apache Tika text extraction, qpdf validation, ffprobe metadata extraction, Sleuth Kit file listing, ALEAPP/iLEAPP extraction analysis, binwalk firmware inspection, guestfish read-only image access, and PhotoRec image recovery.

The adapters intentionally do not use `shell=True`. The osquery adapter rejects non-SELECT statements and multi-statement input. Guestfish is forced to `--ro`. These constraints are part of the code, not documentation-only expectations.

### Platform/API contracts

`packages/integrations/platforms.py` implements deterministic request specifications for TheHive, Velociraptor, OpenCTI, MISP, Censys, Shodan, URLhaus, VirusTotal, official social-profile APIs, and Qdrant vector search. IDs and query values are encoded before insertion into URLs. Request bodies use deterministic JSON serialization.

No live service is falsely marked as end-to-end verified. These entries remain `adapter_contract` until a controlled integration environment provisions the service and credentials and passes a live test.

### Web and infrastructure intelligence

`packages/integrations/web_intel.py` implements public HTTP(S) request validation, DNS query command contracts, and offline parsing of Nmap XML evidence. Credential-bearing URLs are rejected. The Nmap path parses previously produced XML and does not initiate active scanning.

### Linguistic and semantic primitives

`packages/forensic_core/nlp.py` implements Unicode-normalized tokenization, token-frequency vectors, cosine text similarity, deterministic stylometric measurements, and explicit phrase-overlap detection. These functions produce analytical signals only; they do not assert authorship, identity, guilt, or attribution.

### Advanced graph analytics

`packages/forensic_core/advanced_graph.py` implements deterministic connected components, normalized degree centrality, Jaccard-neighbor similarity, and shortest-hop calculation over an explicit in-memory adjacency model.

### Legal-control primitives

`packages/forensic_core/legal.py` implements timezone-aware legal-basis validity, consent receipts, fail-closed authority requirements, deterministic evidence checklists, and explicit admissibility-warning flags. The module supports legal workflow controls but does not substitute for legal judgment.

### Security and cryptographic support

`packages/forensic_core/security.py` adds secret redaction, SHA3-256, HMAC-SHA256 integrity/authentication helpers, retention-policy validation, and deterministic backup-manifest verification.

`packages/integrations/crypto_ops.py` adds argument-array contracts for OpenSSL SHA-256 signing, signature verification, RFC-3161 timestamp-query generation, Git revision lookup, and DVC status checks.

`packages/integrations/security_services.py` adds adapter contracts for Vault Transit signing, S3 Object Lock COMPLIANCE configuration, Sigstore/cosign verification, Restic repository checks, and PKCS#11 private-key URIs.

External cryptographic services and hardware are not reported as live-verified merely because their adapter contract exists.

### Authentication

`packages/integrations/auth.py` implements OIDC discovery/userinfo request contracts and deterministic WebAuthn assertion payload construction. It does not claim to replace a conforming OIDC/WebAuthn verifier.

### Streaming and sensor fusion

`packages/forensic_core/streaming.py` implements timezone-aware events, deterministic ordered-sequence detection, and weighted sensor fusion with strict weight validation.

### Adversarial validation

`packages/forensic_core/simulation.py` implements a non-networked ATT&CK-style validation plan and control-result evaluator. The model is hard-restricted to `lab_only=True` and requires an authorization reference. It does not execute CALDERA, Atomic Red Team, exploitation, scanning, or remote commands.

This distinction is deliberate: the roadmap capabilities for red teaming/attack simulation receive a safe local simulation implementation path, not an unrestricted offensive execution path.

## Executed local tests before repository writes

The newly added second-half behavior suite was executed locally after the implementation files were generated and before they were written to GitHub.

Result: 11 tests passed, 0 failed, 0 errors.

The tests cover NLP/stylometry, graph analytics, legal fail-closed behavior, SHA3/HMAC/backup verification, streaming/sensor fusion, shell-free defensive CLI construction, platform request construction, S3/Restic/PKCS#11 contracts, OIDC/WebAuthn and passive web/Nmap parsing, OpenSSL command construction, and lab-only simulation enforcement.

## Full-catalog gate

`packages/capabilities/tests/test_coverage.py` now requires:

1. exactly 304 implemented capability entries;
2. exactly 100.0% calculated catalog coverage;
3. exact identifier equality with `set(range(1, 305))`;
4. importability of every referenced implementation module;
5. an explicit audited support level for every entry.

The existing GitHub Actions workflow discovers this test suite automatically under `packages/capabilities/tests` after compiling all Python sources and running the evidence-core, forensic-core, and integration suites.

## Residual risks and non-claims

100% catalog coverage means every roadmap capability has an executable implementation path or a concrete external adapter contract. It does **not** mean every third-party technology is installed in GitHub Actions, every commercial service is licensed, every API credential is provisioned, every external service has passed a live end-to-end test, or every capability is production-certified for a legal proceeding.

Capabilities backed by `adapter_contract` remain intentionally distinct from `verified_local`. Promotion to live verification requires a separately audited integration environment, pinned third-party versions, fixture/evidence provenance, failure-mode tests, and repeatable end-to-end evidence.
