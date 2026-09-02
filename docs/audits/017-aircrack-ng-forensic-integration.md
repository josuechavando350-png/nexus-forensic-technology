# Audit 017 — Aircrack-ng forensic integration

## Scope

This audit certifies the read-only Aircrack-ng integration added in `packages/integrations/aircrack_ng.py`.

The integration parses standard `airodump-ng` CSV exports into immutable access-point and station records. It does not execute Aircrack-ng, capture radio traffic, inject frames, deauthenticate clients, recover credentials, or transmit wireless signals.

## Implementation checks

- Standard-library-only parser; no new runtime dependency.
- Bounded input size: 16 MiB maximum.
- UTF-8 BOM handling and surrogate-preserving decoding for local evidence files.
- Strict MAC-address validation for AP and station identifiers.
- Integer validation for channel, speed, power, beacon, IV, and packet counters.
- Explicit support for the `(not associated)` station sentinel.
- Immutable result models (`frozen=True`, `slots=True`).
- Malformed or truncated evidence raises `AirodumpParseError`; invalid rows are not silently discarded.
- Local file loading is read-only and raises `FileNotFoundError` for missing evidence.

## Test coverage

`packages/integrations/tests/test_aircrack_ng.py` verifies:

1. valid AP and station parsing;
2. associated and unassociated stations;
3. probe ESSID preservation;
4. malformed BSSID rejection;
5. truncated row rejection;
6. unrecognized pre-header data rejection;
7. local-file loading;
8. explicit missing-file behavior.

## Repository gates

The existing `quality` workflow covers this module through:

- `python -m compileall -q packages`;
- `python -m unittest discover -s packages/integrations/tests -v`.

Merge is allowed only after the pull-request checks are green and the final PR diff has been reviewed for unintended changes.
