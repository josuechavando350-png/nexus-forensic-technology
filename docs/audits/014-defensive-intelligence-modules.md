# Audit 014 — Defensive intelligence modules

## Scope
This audit covers five defensive capabilities requested for NEXUS Investigation OS:

1. Memory/network telemetry triage.
2. Passive public infrastructure lookup.
3. Evidence-link graph construction and path analysis.
4. Real EXIF GPS extraction.
5. Passive CTI indicator reputation lookup.

## Corrections applied to the submitted examples

- The telemetry module does not claim to detect a kernel exploit from three byte strings. It reports deterministic indicators found in supplied evidence and suspicious destination ports. A positive result is `SUSPICIOUS`, not proof of compromise.
- The infrastructure module does not use a fictional JSON response from `arin.net`. It resolves public DNS and queries the public RDAP service at `rdap.org` for registration metadata.
- The graph module does not claim that a shortest path deanonymizes a person. It returns only paths supported by explicitly supplied evidence links.
- The EXIF module never fabricates latitude/longitude from a byte offset. It parses genuine GPS EXIF fields and returns `None` when GPS metadata is absent.
- The CTI module does not label an indicator as criminal or as a dark-web actor. It queries the AlienVault OTX indicator endpoint and reports provider observations only. API secrets are read from an explicit argument or `OTX_API_KEY`; no key is committed.

## Security review

### telemetry.py
- Input memory is bounded to 64 MiB.
- Connection IPs and ports are validated before analysis.
- Signature matches are deterministic and do not execute supplied bytes.
- The module never executes shell commands, decodes executable payloads, or modifies a device.

### osint_infrastructure.py
- Input is normalized and IDNA-encoded.
- Only public DNS and RDAP metadata are queried.
- A finite timeout is mandatory.
- No requests are made to application paths on the investigated host.

### entity_graph.py
- Empty and oversized labels are rejected.
- Only supplied edges become graph relations.
- Path search catches `NetworkXNoPath` and does not invent links.

### metadata_forensics.py
- Parsing occurs in memory and does not write evidence to disk.
- Invalid/non-image evidence raises a controlled `ValueError`.
- GPS ranges are validated before return.
- Positive tests generate a JPEG with genuine GPS EXIF metadata and verify decoded coordinates.

### threat_intel.py
- Indicator and timeout are validated before network access.
- HTTPS is used for the OTX API.
- No API key is stored in source.
- The return model deliberately exposes provider counts rather than a guilt/risk verdict.

## Test gate
The `defensive-intel` GitHub Actions workflow performs:

1. pinned dependency installation;
2. Python bytecode compilation;
3. `mypy --strict` over the new package;
4. unit tests covering telemetry, graph behavior, real EXIF GPS parsing, and CTI input validation.

Public DNS/RDAP and OTX are real adapters but are not labeled E2E-certified by this audit because CI does not rely on mutable third-party network availability. A future dedicated integration gate may certify those endpoints separately.

## Acceptance
This block is accepted only when both repository `quality` and the `defensive-intel` workflow are green. Any failing type check, compile step, or test blocks merge.
