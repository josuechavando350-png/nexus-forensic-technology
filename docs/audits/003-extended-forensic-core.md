# Audit 003 — Extended Forensic Core

## Scope

This audit covers ten additional executable modules added after Audit 002:

- `merkle.py`
- `case_store.py`
- `indicators.py`
- `correlation.py`
- `acquisition.py`
- `anomaly.py`
- `collection.py`
- `privacy.py`
- `packaging.py`
- `search.py`

No module contains placeholder bodies, TODO implementations, empty adapters, or hard-coded success responses.

## Review results

### merkle.py

Implements domain-separated SHA-256 Merkle hashing. Leaf and internal-node prefixes differ, odd levels duplicate the final node deterministically, and the empty-tree result is stable.

Result: PASS.

### case_store.py

Implements a real SQLite case/evidence store with foreign-key enforcement, primary keys, transactional context managers, deterministic evidence ordering, duplicate-case rejection, and rejection of attachments to nonexistent cases.

Residual risk: SQLite is a local persistence layer and is not represented as a replacement for Neo4j, PostgreSQL, TheHive, or a multi-user case platform.

Result: PASS.

### indicators.py

Implements canonical parsing for IP addresses, domains, and HTTP(S) URLs. IP values use the standard-library `ipaddress` parser; domains are validated and IDNA-normalized; URL fragments are removed and default ports are canonicalized.

Residual risk: canonicalization does not perform reputation lookup, DNS resolution, scanning, or attribution.

Result: PASS.

### correlation.py

Implements exact cross-case correlation from explicitly supplied normalized indicators. Only indicators present in more than one case create links. Pair and indicator output is sorted.

Residual risk: a shared indicator is a correlation signal, not proof that two cases have the same actor.

Result: PASS.

### acquisition.py

Implements read-only chunked SHA-256 hashing of existing regular files. The file is opened only in binary read mode and no source bytes are modified.

Residual risk: this is hashing/manifest acquisition only; it is not a physical-disk imaging implementation and does not claim EWF/Guymager equivalence.

Result: PASS.

### anomaly.py

Implements population z-scores with stable handling of constant series and explicit positive anomaly thresholds.

Residual risk: z-score outliers are statistical signals only. No criminal, fraud, or threat classification is inferred.

Result: PASS.

### collection.py

Implements an in-memory priority queue with duplicate-task rejection and deterministic tie-breaking by task identifier.

Residual risk: it prioritizes already-authorized tasks only; it does not grant collection authority or acquire data.

Result: PASS.

### privacy.py

Implements explicit-range redaction and basic email/phone candidate detection. Redaction rejects overlapping or invalid ranges.

Residual risk: regex detection is intentionally described as basic contact-data detection and must not be represented as full PII discovery or as a replacement for Microsoft Presidio.

Result: PASS with documented limitation.

### packaging.py

Implements deterministic SHA-256 package manifests for supplied byte payloads. Paths are required to be safe relative POSIX paths and path traversal is rejected.

Residual risk: this is a deterministic package manifest primitive and does not yet claim BagIt or in-toto format compliance.

Result: PASS.

### search.py

Implements a local BM25 retrieval index with explicit parameters, deterministic result tie-breaking, tokenization, document-frequency calculation, and score-based ranking.

Residual risk: this is a local retrieval primitive and does not claim OpenSearch feature or scale parity.

Result: PASS.

## Executed verification before repository write

Command:

`python -m unittest discover -s packages/forensic_core/tests -v`

Combined result after Audit 002 and Audit 003 code:

- 19 tests executed
- 19 passed
- 0 failures
- 0 errors

The same package is compiled by CI through `python -m compileall -q packages`.

## Audit principle

A local primitive is not counted as an external technology integration merely because it addresses a similar concept. Neo4j, PostGIS, OpenSearch, Splink, PyMC, OpenCTI, Timesketch, OPA, BagIt, in-toto, and the other roadmap technologies require separate real integrations and separate audits before being marked integrated.

## Gate

This slice is accepted only if GitHub Actions passes both the original evidence-core suite and the complete forensic-core suite.
