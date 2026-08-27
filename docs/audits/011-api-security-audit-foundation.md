# Audit 011 — API Security, Immutable Audit, and Async Ingestion Foundation

## Scope

This audit covers the requested NEXUS Investigation OS application foundation: strict environment configuration, password/JWT security, tamper-evident audit logging, Celery/Redis orchestration, and the protected FastAPI evidence-ingestion endpoint.

The implementation is intentionally limited to defensive evidence handling and authorized case ingestion. It does not perform target exploitation, interception, credential acquisition, unauthorized tracking, or automatic criminal attribution.

## Source alignment

The implementation follows the supplied NEXUS production-code material for immutable SHA-256 audit chaining, Celery/Redis background processing, JWT/Bcrypt route protection, and FastAPI evidence ingestion. It also corrects defects explicitly visible in the source material rather than reproducing them.

## Secret-management decision

The repository is public. Therefore a real `.env` file is not committed. `.gitignore` explicitly excludes `.env`, and `.env.example` contains the exact sample values requested so operators can create a local runtime `.env` without publishing secrets.

This is a security correction, not an omission. Production deployments must replace every sample credential and JWT secret before exposure.

## `config.py`

- Uses `pydantic-settings` and Pydantic v2.
- Every requested setting is required and typed as `str`.
- Blank values are rejected.
- JWT secrets shorter than 32 bytes are rejected.
- Neo4j and Redis URI schemes are validated.
- `.env` is loaded with case-sensitive keys.

## `auth.py`

- Bcrypt is configured through `passlib.context.CryptContext`.
- Password hashing rejects short passwords.
- Password verification fails closed for malformed hashes.
- JWTs use HS256, UTC-aware `iat`/`exp`, an eight-hour TTL, a subject, and the `analista_tactico` role.
- Protected-route validation requires the core claims and distinguishes expired, invalid, and unauthorized-role tokens.

## `auditoria.py`

- Genesis creation uses exclusive file creation and mode `0600`.
- Each record's SHA-256 is computed from a canonical JSON representation containing only the required chain fields.
- New events acquire an OS-level `flock` plus an in-process lock before reading the current tail and appending the next block.
- Writes are appended, flushed, and `fsync`ed before the lock is released.
- The previous block is verified before extension; a corrupted tail stops new writes instead of silently extending a broken chain.
- `verificar_integridad()` walks the full chain and detects changed content, broken indexes, and broken predecessor hashes.

This is tamper-evident logging, not immutable/WORM storage. An administrator with filesystem access can still delete or replace the complete log. WORM/Object Lock and signed timestamps remain separate certification work.

## `tasks.py`

- Celery uses the configured Redis URL for broker and result backend.
- JSON is the only accepted task/result serialization format.
- UTC, late acknowledgements, task tracking, and single-item prefetch are configured.
- The task validates the evidence SHA-256, telephone shape, and the mathematical CLABE check digit before accepting work.
- Logs redact the full telephone and CLABE and expose only suffixes.
- The task currently certifies queue/orchestration and input validation only. It does not falsely claim that external FININT or multimedia engines ran.

## `main.py`

- `/api/v1/auth/login` issues signed JWTs only after credential validation.
- The current bootstrap login uses the configured Neo4j username/password as the initial operator credential because no separate identity-store credential was supplied. This must be replaced by a dedicated identity provider or analyst account store before multi-user production deployment.
- `/api/v1/investigar` requires a valid bearer token.
- Uploaded evidence is SHA-256 hashed incrementally in 1 MiB chunks with a hard 50 MiB limit, avoiding an unbounded in-memory read.
- Empty evidence, malformed telephone values, and invalid CLABEs are rejected.
- Audit records include the evidence hash, byte count, content type, case ID, and authenticated analyst subject; phone and CLABE are not copied into the audit action string.
- Celery enqueue failure returns HTTP 503 and produces a secondary audit event when possible.
- A successful enqueue returns HTTP 202 with case ID, task ID, evidence hash, and audit-chain hash.

## Source defects corrected

The supplied production-code PDF contains a call to `_escribir_recording` even though the class defines `_escribir_registro`; this implementation does not reproduce that defect. It also avoids embedding a JWT key directly in Python source and avoids using floating local configuration when validated environment settings are available.

## Automated tests

The CI suite covers:

1. Bcrypt hashing and positive/negative verification.
2. Required JWT claims and eight-hour-expiration ordering.
3. Genesis creation and two-event hash chaining.
4. Detection of modified audit content.
5. CLABE checksum validation.
6. Direct Celery task execution with synthetic authorized data only.
7. Rejection of invalid login credentials.
8. Successful login followed by protected multipart evidence ingestion.
9. Exact SHA-256 comparison for the uploaded synthetic evidence.
10. Rejection of an unauthenticated investigation request.

The API test mocks only the Celery transport enqueue boundary so CI does not require a running Redis service. It does not mock password, JWT, SHA-256, audit-chain, request parsing, authentication, or CLABE logic. A live Redis/Celery E2E certification remains a separate gate.

## Acceptance gate

This audit is accepted only when the pull-request head passes:

- repository `quality`,
- `api-foundation / certify-api-foundation`, including Python compilation,
- strict mypy checking for the five Python modules,
- all API foundation unit/integration tests.

Until all required checks are green, this document records implementation and review work only and does not claim certification.

## Residual risks and next certifications

- Replace bootstrap Neo4j credentials with a dedicated OIDC/analyst identity store.
- Move secrets to GitHub/environment secrets or Vault and rotate all sample values.
- Certify Redis and Celery against live services.
- Add WORM evidence storage, external trusted timestamping, signed audit checkpoints, rate limiting, malware-safe upload quarantine, and persistence of original evidence bytes.
- Add Neo4j case-graph ingestion only after a separate authorization and provenance design is audited; no suspect identity should be asserted solely from a phone number, bank account, or uploaded artifact.
