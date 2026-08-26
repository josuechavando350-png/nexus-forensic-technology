# NEXUS Forensic Technology

Forensic investigation engine focused on evidence integrity, provenance, reproducible analysis, and auditable human review.

Current implemented foundation:

- SHA-256 evidence integrity records and byte verification
- hash-linked chain of custody
- deterministic forensic timelines
- evidence relationship graphs and shortest paths
- transparent identity-text candidate matching
- Bayesian update and source-reliability weighting primitives
- fail-closed authorization scopes
- geospatial distance/radius primitives
- exact `Decimal` financial-flow aggregation
- deterministic report serialization and report hashing

Every implemented slice requires executable tests and a written audit under `docs/audits/` before the next slice is accepted.

The engine does not treat a statistical score, graph link, identity candidate, or hypothesis probability as proof of identity, guilt, attribution, or legal admissibility. External technologies listed in the project roadmap are only considered integrated after a real adapter/service implementation and its own audit.
