# Audit 007 — Data Foundation End-to-End Certification

## Scope

This audit covers the first live-service certification slice after the 304-capability foundation was merged to `main`.

Services in scope:

1. PostgreSQL 16 + PostGIS 3.4
2. Neo4j 5.24 Community
3. OpenSearch 2.17.1

The purpose is to replace contract-only confidence with executable end-to-end verification against real service processes started in CI.

## Files reviewed

- `infra/data-foundation/docker-compose.yml`
- `packages/integrations/tests/test_data_foundation_e2e.py`
- `.github/workflows/data-foundation-e2e.yml`
- existing production adapters:
  - `packages/integrations/geospatial.py`
  - `packages/integrations/graph.py`
  - `packages/integrations/search.py`

## Line-level findings

### Reproducible infrastructure

The compose file pins explicit service versions instead of floating `latest` tags. Credentials are test-only fixed values and are not represented as production secrets. Each service is exposed only for the ephemeral CI/local certification stack.

PostGIS is provisioned with a dedicated test database and health check. Neo4j is started with explicit authentication. OpenSearch runs single-node with its security plugin disabled only for this disposable certification environment so the test measures the adapter protocol rather than TLS/bootstrap configuration.

### PostGIS certification

The test waits for a real PostgreSQL connection, creates the PostGIS extension, creates a geometry table, inserts two real point geometries, calls the existing `PostGISAdapter.distance_m`, and verifies a zero-distance identity case.

It then calls `PostGISAdapter.points_within_radius` against the real table and requires the nearby point to be returned while the distant point is excluded.

No SQL result is mocked in this test.

### Neo4j certification

The test creates a real Neo4j driver and verifies connectivity before execution. It writes an isolated three-node graph, calls the existing `Neo4jAdapter.neighbors`, and requires the expected relationship result.

It then calls `Neo4jAdapter.shortest_path` and requires the exact path `A -> B -> C` from the live database.

No Neo4j session or record object is mocked in this test.

### OpenSearch certification

The test creates a real temporary index, writes a forensic evidence document through the existing `OpenSearchAdapter.index_document`, performs an explicit index refresh, and searches through `OpenSearchAdapter.search_text`.

The test requires exactly one hit with the expected document identifier and source body, then removes the temporary index.

No OpenSearch response is mocked in this test.

### Readiness and cleanup

Service readiness is bounded by a monotonic 90-second timeout per dependency and preserves the last exception as diagnostic context. The workflow always tears down containers and volumes, including on test failure.

Failure paths capture service logs before cleanup.

## Dependency controls

The CI workflow pins Python client versions:

- `psycopg[binary] == 3.2.1`
- `neo4j == 5.24.0`
- `opensearch-py == 2.7.1`

The service images are also pinned. This prevents an unreviewed upstream `latest` release from silently changing the certification target.

## Security boundaries

This stack contains only synthetic test data. It does not collect, track, enrich, or query real persons. It performs no internet-scale scanning, credential acquisition, interception, or surveillance.

The OpenSearch security plugin is disabled solely in the isolated disposable CI stack. A production deployment must use authentication, TLS, access control, secrets management, audit logging, and network isolation; this audit does not certify those production controls.

## Acceptance gate

This slice is accepted only when the `data-foundation-e2e` GitHub Actions workflow is green on the PR head and all three live-service tests pass.

Until that run succeeds, this document records the code review but does not claim end-to-end certification.

## Residual risks

- Docker image availability remains an external dependency of CI.
- This test certifies the adapter operations exercised here, not every feature of PostgreSQL/PostGIS, Neo4j, or OpenSearch.
- Production security configuration is intentionally outside this first data-functionality certification slice and requires a separate audited hardening stage.
- Performance, high availability, backup/restore, migrations, and large-dataset behavior are not certified by this slice.
