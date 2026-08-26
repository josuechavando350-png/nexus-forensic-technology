# Audit 007 — Data Foundation End-to-End Certification

## Scope

This audit covers the first live-service certification slice after the 304-capability foundation was merged to `main`.

Services in scope:

1. PostgreSQL 16 + PostGIS 3.4
2. Neo4j 5.24.2 Community
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

PostGIS is provisioned with a dedicated test database and health check. Neo4j is started with explicit authentication. OpenSearch runs single-node with its security plugin disabled only for this disposable certification environment so the test measures the adapter protocol rather than production TLS/bootstrap configuration.

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

### Unit/E2E isolation correction

The first quality run failed because normal integration-test discovery imported the live E2E module before the dedicated workflow had installed `psycopg`, `neo4j`, and `opensearch-py`.

The correction moved optional client imports into `setUpClass` and requires `NEXUS_RUN_DATA_FOUNDATION_E2E=1` before live tests execute. Normal unit discovery now skips the E2E class without importing external clients, while the dedicated E2E workflow explicitly enables it.

This preserves a strict separation between fast contract tests and service-backed certification tests.

### OpenSearch bootstrap correction

The first live OpenSearch attempt did not start because OpenSearch 2.17.1 requires an initial admin password when the demo security installer is enabled. The container logs exposed the failure directly.

The isolated E2E stack was corrected to set `DISABLE_INSTALL_DEMO_CONFIG=true` and `DISABLE_SECURITY_PLUGIN=true`. This is limited to synthetic CI certification. It is not a production security configuration.

The Neo4j image was also tightened from the patch-floating `5.24-community` tag to the explicit `5.24.2-community` tag observed during the failed run.

## Dependency controls

The CI workflow pins Python client versions:

- `psycopg[binary] == 3.2.1`
- `neo4j == 5.24.0`
- `opensearch-py == 2.7.1`

The service images use explicit release tags. No `latest` image is used.

## Security boundaries

This stack contains only synthetic test data. It does not collect, track, enrich, or query real persons. It performs no internet-scale scanning, credential acquisition, interception, or surveillance.

The OpenSearch security plugin is disabled solely in the isolated disposable CI stack. A production deployment must use authentication, TLS, access control, secrets management, audit logging, and network isolation; this audit does not certify those production controls.

## Executed verification

Final PR-head verification on commit `eeddc193ca5d476a7fabf726377ede73c8b61dcf`:

- `quality` workflow run 70: **success**
- `data-foundation-e2e` workflow run 4: **success**
- live PostGIS adapter test: **passed**
- live Neo4j adapter test: **passed**
- live OpenSearch adapter test: **passed**
- service cleanup step: **passed**

No mocked service response was used for the three certification tests.

## Acceptance gate

**PASSED.**

This slice is accepted as end-to-end verified for the exact adapter operations exercised by the three live tests.

## Residual risks

- Docker registry/image availability remains an external dependency of CI.
- This certification covers the adapter operations exercised here, not every feature of PostgreSQL/PostGIS, Neo4j, or OpenSearch.
- Production security configuration is intentionally outside this first data-functionality certification slice and requires a separate audited hardening stage.
- Performance, high availability, backup/restore, migrations, and large-dataset behavior are not certified by this slice.
