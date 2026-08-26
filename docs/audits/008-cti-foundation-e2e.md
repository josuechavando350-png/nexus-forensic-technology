# Audit 008 — CTI Foundation End-to-End Certification

## Scope

This audit covers live-service certification for the CTI foundation using OpenCTI and MISP.

The acceptance rule is strict: neither platform is upgraded from adapter-contract confidence to end-to-end confidence until GitHub Actions starts a real service stack, exercises the existing production adapter against that service, and the complete workflow is green.

## OpenCTI

The certification stack pins OpenCTI platform version `7.260824.0` and its supporting Redis, Elasticsearch, MinIO, and RabbitMQ images. The test waits for the real OpenCTI health endpoint, then calls the existing `OpenCTIAdapter.graphql` against `/graphql` using the configured bearer token.

The GraphQL request asks the running platform for the authenticated user and verifies a non-empty user identifier plus the configured synthetic administrator email. No HTTP response is mocked.

## MISP

The certification stack pins MISP Core `v2.5.44`, MariaDB 10.11.13, and Valkey 7.2.11. The test waits for the real MISP heartbeat endpoint, creates a synthetic MISP event through PyMISP, writes a synthetic `domain` attribute, and then invokes the existing `MISPAdapter.search_attributes` against the live platform.

The search must return the exact synthetic value `nexus-certification.invalid`. The event is deleted after verification. No PyMISP search result is mocked.

## Data and safety boundary

Only synthetic, reserved/non-routable certification values are used. The workflow does not collect, enrich, track, identify, or query real people. It does not perform scanning, interception, credential acquisition, or external target discovery.

## Dependency controls

Platform and dependency images are explicitly versioned instead of using floating `latest` tags. Python client versions are pinned in the workflow. Credentials and tokens in these compose files are disposable CI-only fixtures and must never be reused for production.

## Failure handling

Each certification job captures container logs on failure and always removes containers and volumes. A failing platform remains uncertified regardless of whether its adapter contract tests pass.

## Acceptance gate

This audit is accepted only when both `certify-opencti` and `certify-misp` jobs complete successfully on the PR head, in addition to the repository's normal quality workflow.

Until that occurs, this document records implementation and review work only; it does not claim successful live certification.

## Residual risks

This slice certifies only the adapter operations exercised by the tests. Production TLS, secrets management, access controls, backups, HA, migrations, performance, connector workers, feed ingestion, and large-scale CTI synchronization require separate certification stages.
