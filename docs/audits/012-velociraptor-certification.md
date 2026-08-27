# Audit 012 — Velociraptor live certification

## Scope

This audit covers the Velociraptor integration added to the forensic foundation PR. The acceptance rule is deliberately narrow: the repository may claim Velociraptor certification only if the real pinned binary is downloaded, checksum-verified, executed, and used to run an allowlisted read-only VQL query in CI.

## Source and binary integrity

- Version pinned: `v0.77.2`.
- Linux amd64 release asset: `velociraptor-v0.77.2-linux-amd64`.
- Expected SHA-256: `6c4c23c466d892788ff56ddcd3a31f844e4c0d797ade454c5e2625eb9e427077`.
- CI refuses to continue when the downloaded bytes do not match that digest.
- The binary is executed directly from `/tmp/velociraptor`; no shell interpolation is used by the Python adapter.

## Adapter review

`packages/integrations/velociraptor_cli.py` exposes only two operations:

1. `velociraptor_version()` executes the binary's `version` command and rejects non-zero or empty responses.
2. `velociraptor_query()` accepts a symbolic query name rather than arbitrary VQL. The query text is selected from the module-owned `_SAFE_QUERIES` map.

The initial allowlist contains:

- `host_info`: host operating-system and architecture metadata from `info()`.
- `processes`: process metadata from `pslist()`.

Arbitrary user-supplied VQL is not passed to Velociraptor. This is intentional: a general VQL execution surface would exceed the read-only forensic integration boundary and could expose plugins or functions with side effects.

## Output validation

Velociraptor is invoked with `--format=jsonl`. Every non-empty output line is decoded independently. Certification fails if:

- the command returns non-zero;
- a line is not valid JSON;
- a decoded row is not a JSON object;
- the query returns zero rows.

## End-to-end certification

`test_velociraptor_e2e.py` is disabled by default and runs only when `NEXUS_RUN_VELOCIRAPTOR_E2E=1`. CI sets this flag after installing and checksum-verifying the pinned real binary.

The live test requires:

- real version output containing `0.77.2`;
- a real `host_info` VQL execution;
- at least one returned row;
- non-empty `OS` and `Architecture` values;
- rejection of a string attempting to inject an arbitrary `execve()` VQL expression.

No Velociraptor stdout is mocked in this certification path.

## Failure handling

- Missing executable: surfaced by `subprocess` as a hard test failure.
- Timeout: surfaced by `subprocess.TimeoutExpired` as a hard failure.
- Non-zero exit: converted into `RuntimeError` preserving stderr where available.
- Malformed JSONL: converted into `RuntimeError` with the offending line number.
- Unsupported query name: rejected before process execution with `ValueError`.

## Residual risks and explicit non-claims

This gate certifies local command-line VQL execution with the pinned Velociraptor binary. It does **not** yet certify a deployed Velociraptor frontend/client fleet, mTLS enrollment, hunts, remote collections, server datastore persistence, or production RBAC. Those require separate infrastructure certification and must not be inferred from this audit.

## Acceptance

Velociraptor is accepted for this phase only after GitHub Actions reports `certify-velociraptor` successful on the exact PR head that contains this audit and implementation.
