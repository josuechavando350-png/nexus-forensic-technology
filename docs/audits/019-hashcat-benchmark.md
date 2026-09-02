# Audit 019 — Hashcat benchmark telemetry

## Scope

Real Hashcat integration restricted to synthetic benchmark mode. It measures device hashing throughput without accepting target hashes, wordlists, masks, recovered credentials, potfiles, or attack sessions.

## Verified implementation properties

- Exact command construction uses `--benchmark`, a numeric `--hash-type`, `--machine-readable`, and `--quiet` only.
- No target-hash path or candidate-password input is accepted by the API.
- Machine-readable benchmark records preserve device ID, Hashcat metadata fields, execution runtime, and hashes/second.
- Malformed, negative, empty, timed-out, and non-zero command results are explicit errors.
- Hash-mode input is type/range validated.

## Tests

`packages/forensic_core/tests/test_hashcat_benchmark.py` validates documented machine-readable benchmark parsing, exact safe argv construction, mode validation, and malformed/negative telemetry rejection.

## Certification gate

Merge only after the global quality suite and all PR checks complete successfully and the final diff contains only this implementation, tests, and audit record.
