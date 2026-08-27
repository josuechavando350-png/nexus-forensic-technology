# Audit 010 — Volatility 3 End-to-End Certification

## Scope

This audit covers the first live certification slice for Volatility 3 through the existing `volatility_command` adapter in `packages/integrations/defensive_cli.py`.

The acceptance rule is strict: Volatility is not considered end-to-end certified unless GitHub Actions installs a pinned real Volatility 3 package, invokes the real `vol` executable through the production adapter contract, scans a real local memory-image file, and returns the expected synthetic kernel-banner evidence with exit code zero.

## Adapter review

The existing adapter accepts exactly two caller-controlled inputs: a local memory-image path and a plugin name. The plugin string must be nonblank and is restricted to alphanumeric characters plus `.`, `_`, and `-`, preventing shell metacharacters from entering the command specification. The memory-image input is passed through `require_safe_local_path`. The returned command is an argv tuple rather than a shell string: `vol -f <image> <plugin>`.

This certification deliberately executes the argv with `subprocess.run(..., shell=False)` so command parsing remains structural and no shell expansion is introduced by the test harness.

## Synthetic evidence construction

The test creates a temporary raw file containing only zero-filled bytes plus one deterministic synthetic Linux kernel banner:

`Linux version 6.8.0-nexus-certification #1 SMP PREEMPT_DYNAMIC`

The file contains no captured memory, credentials, personal information, external target data, or third-party evidence. It exists only for the lifetime of the test temporary directory.

## Live tool behavior

GitHub Actions installs the pinned package `volatility3==2.26.2` and verifies that the `vol` executable is available. The test then builds the command through the production `volatility_command` adapter using plugin `banners.Banners` and runs that command against the synthetic raw image.

Acceptance requires all of the following:

1. the adapter produces the expected argv in the expected order;
2. the real `vol` process exits with code `0`;
3. Volatility output contains the exact synthetic kernel-banner marker.

No subprocess result, Volatility output, memory layer, scanner result, or plugin response is mocked.

## Failure behavior

Any nonzero process status fails the test and includes stdout/stderr in the assertion message. If Volatility changes CLI semantics, plugin discovery, banner scanning, or package behavior incompatibly, this certification fails rather than silently accepting the change.

## Security and evidence boundary

This test is offline and local. It performs no acquisition, live-memory capture, endpoint collection, network access to a target, persistence, process manipulation, credential extraction, or user tracking. Its purpose is only to prove that the NEXUS adapter can invoke a real Volatility analysis path against synthetic evidence.

## What this certifies

This slice certifies:

- installation of the pinned Volatility 3 runtime in CI;
- executable discovery for `vol`;
- adapter-to-CLI argument compatibility;
- real raw-file ingestion;
- execution of the real `banners.Banners` plugin;
- deterministic recovery of a known synthetic banner.

## What this does not certify

This slice does not claim production support for every Volatility plugin, Windows/Linux/macOS symbol resolution, real incident memory dumps, encrypted/compressed acquisitions, corrupted-memory tolerance, performance on large captures, symbol-server availability, or evidentiary interpretation of process/network artifacts. Those require separate fixtures and audits.

## Acceptance gate

Audit 010 is accepted only when the PR-head `certify-volatility` job passes together with the repository quality checks and already-certified Sleuth Kit regression job.
