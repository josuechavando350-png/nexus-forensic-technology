# Audit 001 — Evidence integrity core

Status: PASS locally; GitHub Actions required before merge.

Scope: `packages/evidence_core/evidence.py` and its tests. This audit covers only deterministic evidence hashing and integrity verification. It does not claim chain of custody, acquisition, attribution, surveillance, or legal admissibility.

## Source alignment

Implements the first narrow slice of NEXUS capabilities 248–249: evidence integrity and SHA-256 hashing. The implementation uses Python `hashlib.sha256`, matching the selected technology for capability 249.

## Line-by-line review findings

- Future annotations import: deterministic interpreter behavior; no runtime side effect.
- `dataclass(frozen=True, slots=True)`: record fields cannot be reassigned through normal dataclass use and accidental dynamic attributes are blocked.
- `evidence_id`: required and rejected when blank.
- `source_ref`: required and rejected when blank.
- `sha256_hex`: required to be exactly 64 characters and valid hexadecimal.
- `size_bytes`: rejected when negative.
- `sha256_hex(data)`: accepts bytes only and returns the standard lowercase 64-character SHA-256 digest.
- `create_evidence_record`: derives both digest and byte length from the exact byte sequence supplied by the caller; it does not generate timestamps, UUIDs, or mutable metadata.
- `verify_evidence_bytes`: rejects wrong types, fails immediately on size mismatch, and uses `hmac.compare_digest` for digest comparison.

## Executed verification

Commands executed against the exact implementation before publication:

`python -m compileall -q packages`

`python -m unittest discover -s packages/evidence_core/tests -v`

Result: 8 tests executed, 8 passed, 0 failed, 0 errors.

Covered cases:

1. Standard SHA-256 known-answer vector for `abc`.
2. SHA-256 known-answer vector for empty bytes.
3. Evidence record captures byte length and digest.
4. Evidence record is frozen against field reassignment.
5. Blank evidence and source identifiers are rejected.
6. Untampered bytes verify successfully.
7. Same-length tampering fails verification.
8. Invalid digest length and negative byte size are rejected.

## Residual risks

- `frozen=True` provides application-level immutability, not cryptographic sealing of an in-memory Python object.
- This module hashes bytes supplied by a caller; it does not yet implement forensic acquisition or write-blocked device reads.
- SHA-256 proves byte integrity relative to the recorded digest; it does not prove origin, custody, authorship, or admissibility.
- No persistent manifest format exists yet. That will be a separate capability and must receive its own audit before use.

## Gate

No next forensic capability should be added until the pull-request CI for this module passes on Python 3.12.
