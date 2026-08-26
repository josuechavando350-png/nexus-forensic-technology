# Audit 005 — 50% Catalog Checkpoint

## Objective

Establish a mechanically verifiable checkpoint for exactly half of the 304-capability roadmap without claiming capabilities that have no executable code behind them.

## Counting rule

A capability is counted only when `packages/capabilities/coverage.py` points it to one or more importable implementation modules and assigns one of two explicit support levels:

- `verified_local`: executable local behavior exists and is covered by the repository test suites.
- `adapter_contract`: a real external-technology call path exists and its request/query/validation contract is tested, but the live external service is not falsely reported as end-to-end verified.

Documentation-only entries, placeholders, TODOs, empty adapters, conceptual mentions, and technologies that have not received an implementation path do not count.

## Result

- Catalog size: 304 capabilities.
- Counted implementation checkpoint: 152 capabilities.
- Calculated progress: 50.0%.
- Duplicate capability identifiers: 0.
- Coverage entries without implementation references: 0.

The exact count is enforced by executable tests rather than a manually typed percentage.

## Implementation families represented

The 152 counted entries are backed by code across these audited families:

- geospatial analysis and PostGIS/H3 adapter contracts;
- hypothesis testing, Bayesian evidence updating, evidence weighting, source reliability, and confidence support primitives;
- relationship, evidence, cross-case, and knowledge graph primitives plus Neo4j/NetworkX adapter contracts;
- CTI adapter contracts for OpenCTI and MISP;
- local filesystem forensic listing through a read-only Sleuth Kit CLI contract;
- evidence hashing, acquisition, provenance, chain of custody, Merkle roots, deterministic manifests, reproducibility, validation, and packaging;
- read-only Web3 transaction/receipt/balance adapter contracts;
- deterministic forensic timelines;
- financial flow and anomaly primitives;
- normalized domain/IP/URL indicators plus passive RDAP, certificate-transparency, and BGP record handling;
- collection prioritization;
- read-only SQLite/email artifact parsing plus metadata adapter paths;
- BM25/OpenSearch information retrieval;
- cross-case correlation;
- identity/alias/account comparison primitives;
- local anomaly/statistical primitives plus scikit-learn/XGBoost adapter paths;
- Kafka/Spark adapter contracts;
- authorization, privacy, and OPA policy paths;
- deterministic forensic/pericial report encoding;
- local case/evidence persistence for analyst review workflows.

## Non-claims

This checkpoint does not mean 152 capabilities are production-complete in every environment. In particular, an `adapter_contract` entry is not upgraded to live-service verification until CI or a controlled integration environment provisions the external dependency and passes an end-to-end test.

The checkpoint also does not count unimplemented roadmap technologies merely because another module is conceptually related to them. For example, no CALDERA, Atomic Red Team, full mobile-forensics suite, WORM storage, HSM, Sigstore, or live Timesketch service is represented as complete unless code and verification are added separately.

## Tests executed before repository writes

Local verification performed during this implementation sequence:

- forensic core suite: 19/19 passed;
- integration contract suite: 11/11 passed;
- capability coverage suite: 3/3 passed.

Earlier evidence-core verification remains independently enforced by CI.

## CI gate

The workflow now runs, in order:

1. compile every Python source under `packages`;
2. evidence integrity tests;
3. forensic core tests;
4. integration contract tests;
5. exact capability coverage checkpoint tests.

The 50% checkpoint is accepted only when this complete workflow is green on the PR head.
