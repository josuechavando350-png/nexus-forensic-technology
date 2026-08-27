# Audit 013 — Security foundation: isolation, ML-DSA-65, sensor fusion, external anchoring

## Scope

This audit covers the implementation requested for capability references #294, #295, #247, #250, #219, #221, #296 and #298. The submitted snippets were treated as design input, not copied blindly where they made security claims the code did not actually satisfy.

## 1. Zero Trust / least privilege

Implemented in `packages/security_foundation/zero_trust.py`.

- Rejects execution as UID 0 on POSIX systems.
- Rejects payloads larger than 1 MiB before spawning a worker.
- Spawns a separate isolated Python process with `-I -S`, a minimal environment, temporary working directory, no shell, timeout and POSIX resource limits for CPU, address space, core dumps and file descriptors.
- Parent independently recomputes SHA-256 and validates the child result.
- The API deliberately reports `PROCESS_ISOLATED`, not `SANDBOX_ISOLATED`, because process separation and resource limits are not equivalent to a kernel sandbox, VM, seccomp profile or hardened container.

Residual boundary: production execution of attacker-controlled executable code would still require a stronger sandbox boundary. This implementation processes bytes only and does not execute the payload itself.

## 2. Post-quantum evidence signatures

Implemented in `packages/security_foundation/pqc.py` using `pqcrypto==1.0.0` and ML-DSA-65.

The submitted SHA3 + HMAC construction was not labeled or retained as Dilithium/PQC because HMAC-SHA256 is not an ML-DSA signature and a hard-coded master key would be a secret-management failure.

The implementation instead:

- Generates a real ML-DSA-65 public/secret keypair.
- Hashes evidence with SHA3-256 before signing.
- Signs the digest with an application context string.
- Emits algorithm, evidence digest, public key and signature in a typed immutable bundle.
- Verifies both the evidence digest and ML-DSA signature.
- Does not commit a private key to the repository.

Residual boundary: the pinned `pqcrypto` package is a real implementation dependency but its own project documentation states that third-party security review is recommended. Production key custody still requires HSM/KMS/TPM-backed secret storage or another approved key-management boundary.

## 3. Sensor fusion

Implemented in `packages/security_foundation/sensor_fusion.py`.

- Validates numeric finite timestamps.
- Caps each stream at 10,000 events to bound work.
- Correlates events inside a strict five-second window.
- Uses the strongest temporal match per satellite event to prevent duplicate network events from inflating a single source event without bound.
- Returns a normalized 0..100 analytical correlation score.

Critical semantic correction: this score is explicitly not represented as a probability of identity, criminal responsibility or organization membership. Temporal proximity alone cannot support such a claim.

## 4. Tamper-evident audit with external anchor interface

Implemented in `packages/security_foundation/hardware_audit.py`.

- Stores the full append-only JSONL record chain, not only hashes.
- Uses canonical JSON and SHA-256 chaining.
- Verifies index continuity, previous-hash continuity and every record hash before appending.
- Atomically rewrites through a temporary file, `fsync`, mode 0600 and `os.replace`.
- Refuses to accept an on-disk chain whose latest hash differs from the external anchor.
- Rolls back a newly written record if the external anchor update fails.
- Includes `TPM2NVAnchor`, a real adapter for `tpm2_nvread`/`tpm2_nvwrite` against an already-provisioned TPM 2.0 NV index.
- Includes `SoftwareAnchor` only for deterministic local/CI testing and labels it explicitly as not a hardware security boundary.

Residual boundary: CI does not contain a physical TPM, so TPM-backed anchoring is implemented but not hardware-certified in this PR. It must not be described as TPM-verified until an E2E test is executed on a runner with a provisioned TPM 2.0 NV index.

## Automated acceptance tests

`packages/security_foundation/tests/test_security_foundation.py` verifies:

1. isolated payload processing and parent-side integrity validation;
2. rejection of payloads above 1 MiB;
3. rejection of root execution;
4. real ML-DSA-65 sign/verify and tamper rejection;
5. bounded temporal sensor correlation;
6. zero score for empty streams;
7. audit-chain progression and external-anchor synchronization;
8. detection of manual audit-file tampering.

`.github/workflows/security-foundation.yml` installs pinned dependencies, compiles the package, executes strict mypy and runs the test suite. This audit is accepted only when that workflow and the repository's normal quality workflow are green.

## Certification status

- Process isolation / least privilege: pending CI at time of authoring.
- ML-DSA-65 PQC: pending CI at time of authoring.
- Sensor fusion algorithm: pending CI at time of authoring.
- Tamper-evident chain with software test anchor: pending CI at time of authoring.
- Physical TPM 2.0 hardware anchoring: adapter implemented, **not E2E-certified** in this PR.
