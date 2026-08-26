# Audit 008 — CTI Foundation End-to-End Certification

## Scope

This audit covers live-service certification for the CTI foundation using OpenCTI and MISP.

The acceptance rule is strict: neither platform is upgraded from adapter-contract confidence to end-to-end confidence until GitHub Actions starts a real service stack, exercises the existing production adapter against that service, and the complete workflow is green.

## OpenCTI

The certification stack pins OpenCTI platform version `7.260824.0` and its supporting Redis, Elasticsearch, MinIO, and RabbitMQ images. The test waits for the real OpenCTI health endpoint, then calls the existing `OpenCTIAdapter.graphql` against `/graphql` using the configured bearer token.

The GraphQL request asks the running platform for the authenticated user and verifies a non-empty user identifier plus the configured synthetic administrator email. No HTTP response is mocked.

The live `certify-opencti` job passed on commit `6cc87c2760e012b93720e5abe654093a834feeb4`, including service startup, GraphQL execution through the production adapter, assertions, and container cleanup.

## MISP

The certification stack pins MISP Core `v2.5.44`, MariaDB 10.11.13, and Valkey 7.2.11. The test waits for an authenticated MISP API request to succeed, creates a synthetic MISP event through PyMISP, writes a synthetic `domain` attribute, and then invokes the existing `MISPAdapter.search_attributes` against the live platform.

The search must return the exact synthetic value `nexus-certification.invalid`. The event is deleted after verification. No PyMISP search result is mocked.

### Defect found during certification

The first live MISP run exposed a real readiness defect: the public heartbeat endpoint became available before first-run database and administrator initialization had completed. The test therefore attempted PyMISP authentication too early and received HTTP 403.

The fix did not hide or retry the failing operation blindly. Readiness was changed to require a successful authenticated request to `/servers/getVersion` using the configured API key. This makes the readiness gate represent the capability the adapter actually needs.

After that correction, `certify-misp` passed on commit `6cc87c2760e012b93720e5abe654093a834feeb4`, including authenticated initialization, synthetic event creation, attribute creation, live adapter search, cleanup, and container teardown.

## Data and safety boundary

Only synthetic, reserved/non-routable certification values are used. The workflow does not collect, enrich, track, identify, or query real people. It does not perform scanning, interception, credential acquisition, or external target discovery.

## Dependency controls

Platform and dependency images are explicitly versioned instead of using floating `latest` tags. Python client versions are pinned in the workflow. Credentials and tokens in these compose files are disposable CI-only fixtures and must never be reused for production.

## Failure handling

Each certification job captures container logs on failure and always removes containers and volumes. A failing platform remains uncertified regardless of whether its adapter contract tests pass.

## Acceptance result

Accepted for the operations exercised by this slice.

On commit `6cc87c2760e012b93720e5abe654093a834feeb4`:

- `quality`: success
- `data-foundation-e2e`: success
- `cti-foundation-e2e`: success
- `certify-opencti`: success
- `certify-misp`: success

This means the existing OpenCTI and MISP adapters now have live end-to-end evidence for the exact operations covered by these tests.

## Residual risks

This slice certifies only the adapter operations exercised by the tests. Production TLS, secrets management, access controls, backups, HA, migrations, performance, connector workers, feed ingestion, and large-scale CTI synchronization require separate certification stages.
