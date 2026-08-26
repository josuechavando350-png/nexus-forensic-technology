# Audit 004 — External Integration Adapters

## Scope

This audit covers the first external-technology adapter layer. Adapters are real call paths with input validation, parameterized queries or structured API requests, deterministic serialization where applicable, and explicit error handling. External services are not falsely reported as end-to-end verified when CI does not provision them.

Modules audited:

- `packages/integrations/graph.py`
- `packages/integrations/geospatial.py`
- `packages/integrations/search.py`
- `packages/integrations/cti.py`
- `packages/integrations/passive_infra.py`
- `packages/integrations/forensics_cli.py`
- `packages/integrations/local_artifacts.py`
- `packages/integrations/blockchain.py`
- `packages/integrations/ml.py`
- `packages/integrations/opa.py`
- `packages/integrations/streaming.py`

## Findings

### graph.py — Neo4j / NetworkX

- Neo4j entity identifiers are passed as query parameters.
- Relationship types, which Cypher does not parameterize, are restricted to identifier-safe characters before interpolation.
- Result limits are bounded.
- Shortest-path depth is bounded to prevent unbounded traversal queries.
- NetworkX is loaded lazily and missing dependency errors are explicit.

Result: PASS for adapter contract. External Neo4j end-to-end verification remains pending.

### geospatial.py — PostGIS / H3

- Latitude and longitude are range checked.
- PostGIS coordinates are passed in longitude/latitude order to `ST_MakePoint`.
- Radius and query limits are bounded.
- Dynamic table/column identifiers are restricted before SQL interpolation; coordinate/radius values remain parameterized.
- H3 resolution is bounded to 0–15 and supports current and legacy Python API names.

Result: PASS for adapter contract. External PostGIS/H3 runtime verification remains pending.

### search.py — OpenSearch

- Index and document identifiers are validated.
- User text is sent through structured `multi_match` query JSON rather than query-string concatenation.
- Result size is bounded.
- Tie ordering uses `_id` after score for stable result order.

Result: PASS for adapter contract. External OpenSearch end-to-end verification remains pending.

### cti.py — OpenCTI / MISP

- OpenCTI requests use GraphQL JSON with variables and bearer authentication.
- GraphQL errors are detected and converted to explicit runtime failures.
- MISP attribute search uses the PyMISP client contract and bounded result limits.

Result: PASS for adapter contract. Live OpenCTI/MISP credentials and service tests are not present in CI and are not claimed.

### passive_infra.py — RDAP / certificate transparency / BGP records

- RDAP domains are normalized and path separators are rejected.
- IP input is parsed with `ipaddress` before request construction.
- Certificate-transparency lookups are passive HTTP queries.
- BGP records are parsed deterministically from supplied records and malformed incomplete entries are skipped.

Result: PASS for adapter contract. No active scanning is implemented.

### forensics_cli.py — ExifTool / ffprobe / Sleuth Kit

- Local input paths must exist.
- Commands are executed with argument arrays and `shell=False`.
- Timeouts are mandatory and positive.
- ExifTool and ffprobe parse structured JSON output.
- Sleuth Kit `fls` is invoked only for read/list analysis of a supplied image path.

Result: PASS for code review. Executable-presence/e2e tests are pending and are not claimed.

### local_artifacts.py — email / SQLite forensic artifacts

- Email parsing uses Python's standards-based email parser over supplied bytes.
- SQLite access uses URI `mode=ro`.
- Only `SELECT` and `PRAGMA` statements are accepted by the helper.

Result: PASS.

### blockchain.py — web3.py client contract

- Transaction, receipt, and balance operations are read-only RPC lookups.
- Empty identifiers are rejected.
- Address normalization delegates to the Web3 checksum implementation.

Result: PASS for adapter contract. No transaction signing or asset transfer is implemented.

### ml.py — scikit-learn / XGBoost

- Dependencies are lazy-loaded and missing packages fail explicitly.
- DBSCAN parameters are validated.
- IsolationForest and XGBoost expose deterministic `random_state` defaults.
- The adapter returns model outputs only; it does not label a person as criminal or establish attribution.

Result: PASS for adapter code review. Model-quality validation is dataset-specific and pending by design.

### opa.py — Open Policy Agent

- Policy paths reject traversal segments.
- OPA input is sent as structured JSON.
- Missing `result` values fail explicitly rather than defaulting to allow.

Result: PASS for adapter contract.

### streaming.py — Kafka / Spark

- Kafka payload JSON is canonicalized before sending.
- Topics and keys must be nonblank.
- Spark DataFrame creation rejects empty record sets.

Result: PASS for adapter contract. Kafka/Spark cluster e2e tests remain pending.

## Executed verification before repository write

Command:

`python -m unittest discover -s packages/integrations/tests -v`

Result:

- 11 tests executed
- 11 passed
- 0 failures
- 0 errors

These tests verify adapter contracts with controlled test doubles and real local SQLite/email parsing. They do not pretend to be live-service tests.

## CI gate

GitHub Actions now runs:

1. `python -m compileall -q packages`
2. evidence-core tests
3. forensic-core tests
4. integration contract tests

No external technology is marked production-verified until a separate environment-backed integration test exists for it.
