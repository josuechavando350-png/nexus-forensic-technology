# Audit 002 — Forensic Core Foundation

## Scope

This audit covers the second implemented slice of NEXUS Forensic Technology. The slice is deliberately limited to deterministic, reviewable primitives that can be verified without external services.

Implemented modules:

- `packages/forensic_core/provenance.py`
- `packages/forensic_core/timeline.py`
- `packages/forensic_core/graph.py`
- `packages/forensic_core/identity.py`
- `packages/forensic_core/hypothesis.py`
- `packages/forensic_core/policy.py`
- `packages/forensic_core/geospatial.py`
- `packages/forensic_core/financial.py`
- `packages/forensic_core/reporting.py`

## Audit rules

1. No placeholder functions, `pass`, TODO implementations, mock return values, or empty adapters are accepted.
2. Inputs that affect evidentiary meaning are validated before processing.
3. Deterministic outputs are preferred wherever ordering is observable.
4. Authorization is fail-closed: an expired or out-of-scope request is denied.
5. Probabilistic outputs are numerical aids only; no module declares identity, guilt, attribution, or legal admissibility.
6. Identity matching exposes its method and score and uses a conservative default threshold.
7. Financial arithmetic uses `Decimal`, not binary floating point.
8. Chain-of-custody events are hash-linked using canonical JSON and SHA-256.
9. Reports are serialized with stable key ordering and reject NaN/Infinity.

## Line-level review findings

### provenance.py

- UTC normalization is explicit and naive timestamps are rejected.
- Canonical JSON fixes key order and separators before hashing.
- Every event incorporates the previous event digest.
- Reconstructed chains are verified during construction.
- A modified historical event fails verification.

Result: PASS.

### timeline.py

- Duplicate event identifiers are rejected.
- Timezone-aware timestamps are mandatory.
- Equal-time events are ordered by identifier for deterministic output.
- Invalid inverted time windows are rejected.

Result: PASS.

### graph.py

- Empty edge fields are rejected.
- Neighbor ordering is deterministic.
- Shortest path uses breadth-first search.
- Component output is sorted to avoid set-order nondeterminism.

Result: PASS.

### identity.py

- Unicode accents are normalized before comparison.
- Exact normalized matches are distinguishable from fuzzy matches.
- Fuzzy scores remain visible to callers.
- Candidate classification requires an explicit threshold and defaults to 0.90.

Residual risk: `SequenceMatcher` is not a production entity-resolution system. It is retained only as an explainable local primitive; external Splink/graph-backed resolution is not claimed as implemented.

Result: PASS with documented limitation.

### hypothesis.py

- Every probability is bounded and finite.
- Bayes update rejects zero-probability evidence under both hypotheses.
- Source reliability moderates evidence toward neutral 0.5 rather than silently amplifying it.
- Competing hypothesis weights are normalized deterministically.

Residual risk: this module does not infer priors or likelihoods. Those values must come from a documented model or analyst input.

Result: PASS.

### policy.py

- Case identifier and all authorization dimensions are mandatory.
- Expiry uses timezone-aware comparisons.
- Purpose, source type, and action must all be explicitly authorized.
- Default behavior for any mismatch is denial.

Result: PASS.

### geospatial.py

- Latitude and longitude ranges are validated.
- Distance uses the haversine formula with a documented mean Earth radius.
- Negative radii are rejected.

Residual risk: spherical distance is not a replacement for PostGIS geodesic calculations where survey-grade precision is required.

Result: PASS with documented limitation.

### financial.py

- Transaction identifiers and accounts are mandatory.
- Negative transaction amounts are rejected.
- Currency codes are normalized during aggregation.
- Duplicate transaction identifiers are rejected.
- Arithmetic uses `Decimal`.

Residual risk: no FX conversion, banking semantics, AML classification, or attribution is inferred.

Result: PASS.

### reporting.py

- Only mappings are accepted as report roots.
- Stable JSON serialization is enforced.
- NaN and Infinity are rejected.
- SHA-256 is calculated from the exact serialized bytes.

Result: PASS.

## Executed verification before repository write

Environment: Python 3.12-compatible standard-library code.

Command:

`python -m unittest discover -s packages/forensic_core/tests -v`

Result:

- 9 tests executed
- 9 passed
- 0 failures
- 0 errors

The repository CI separately recompiles all Python sources and executes both the original evidence-integrity suite and this forensic-core suite.

## Capabilities represented by this slice

This slice provides local primitives for concepts appearing in the supplied 304-capability roadmap, including timeline reconstruction, relationship/link analysis, identity/alias comparison, hypothesis testing, source reliability, geospatial correlation, financial flow analysis, evidence provenance, digital chain of custody, evidence integrity, authorization controls, reproducibility, and forensic reporting.

It does **not** claim that external technologies named in the roadmap (for example Neo4j, PostGIS, Splink, PyMC, OpenSearch, OpenCTI, Timesketch, or OPA) are integrated merely because a corresponding local primitive exists. Those integrations require their own implementation and audit.

## Gate

The next implementation slice may proceed only when:

- repository CI compiles all source files;
- original evidence-core tests pass;
- all 9 forensic-core tests pass;
- no unresolved audit defect is introduced by the commit.
