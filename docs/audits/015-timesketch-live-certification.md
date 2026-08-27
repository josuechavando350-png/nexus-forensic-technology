# Audit 015 — Timesketch live certification

## Scope

This audit covers the NEXUS integration with Timesketch as the fourth forensic-foundation component after Sleuth Kit, Volatility 3 and Velociraptor.

## Implementation reviewed

### `packages/integrations/timesketch.py`

- Uses the official `timesketch-api-client` package rather than a hand-written emulation of the Timesketch protocol.
- Requires an explicit server URI, username and password from the caller; no production credential is embedded in source.
- Rejects blank credentials and unsupported URI schemes before network access.
- Returns immutable sketch summaries containing only server-provided IDs, names and descriptions.
- Does not fabricate timelines, events, identities, findings or analysis results.
- The integration is read-only in this certification slice: it lists sketches visible to the authenticated identity and performs no destructive operation.

### `packages/integrations/e2e/test_timesketch_e2e.py`

- The test is gated by `NEXUS_RUN_TIMESKETCH_E2E=1` so an ordinary unit-test invocation cannot accidentally contact an external service.
- Under the GitHub Actions certification gate, the service endpoint is the locally started Timesketch instance, not a public third-party system.
- Authentication uses the documented development-only `dev/dev` account inside the disposable CI stack.
- Passing requires a real authenticated API request to the running server and successful deserialization through the NEXUS adapter.

### `.github/workflows/forensics-foundation-e2e.yml`

The Timesketch job:

1. installs the pinned official API client `timesketch-api-client==20260611`;
2. checks out the official Timesketch release tag `20260630`;
3. starts the upstream Docker development stack;
4. waits for the upstream readiness marker instead of relying on a fixed sleep;
5. starts the documented Celery worker and Gunicorn web server inside the Timesketch container;
6. waits for the HTTP service to become reachable;
7. executes the authenticated NEXUS E2E test;
8. captures container logs on failure; and
9. always destroys containers and volumes after the run.

## Claims deliberately not made

- Listing sketches does not certify every Timesketch analyzer or importer.
- This test does not claim production hardening, HA, TLS termination or multi-node OpenSearch certification.
- The disposable development account is not a production authentication configuration.
- NEXUS does not claim ownership of Timesketch or equivalence to its complete UI/API surface.

## Resource risk

Upstream documentation recommends at least 8 GB of RAM for the development Docker stack. GitHub-hosted runner capacity can vary. A failure caused by insufficient runner resources is still a failed certification gate and must not be relabeled as success; in that case the correct remediation is a suitably sized runner or a smaller upstream-supported deployment profile, not mocking the server.

## Acceptance

Timesketch is accepted for this integration slice only when the `certify-timesketch` job completes successfully against the pinned real server. The full forensic-foundation PR remains blocked if this job, repository `quality`, or any existing forensic E2E job is red.
