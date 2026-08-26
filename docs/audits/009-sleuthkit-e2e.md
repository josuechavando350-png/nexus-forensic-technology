# Audit 009 — Sleuth Kit End-to-End Certification

## Scope

This audit covers the first live certification in the forensic-tooling layer: The Sleuth Kit `fls` command exercised through the existing `sleuthkit_fls` adapter in `packages/integrations/forensics_cli.py`.

The acceptance rule is strict: this capability is not considered end-to-end certified until GitHub Actions installs the real Sleuth Kit binary, constructs a real filesystem image, invokes the production adapter against that image, and the workflow is green.

## Existing adapter reviewed

`sleuthkit_fls` first requires the supplied image path to exist. It invokes `fls` through the shared `run_read_only_command` helper with `shell=False`, recursive listing (`-r`) and full-path output (`-p`). A non-zero process exit is converted into a runtime error rather than silently returning partial output.

The adapter does not mount, modify, repair, or write to the evidence image.

## End-to-end fixture

The test creates a temporary 16 MiB image and formats it as ext4 using the real `mkfs.ext4` utility. A synthetic text artifact named `nexus-evidence.txt` is inserted into that disposable image with `debugfs` before analysis.

The source artifact contains only the string `NEXUS synthetic forensic certification artifact`. No real evidence or personal data is used.

The fixture-building stage is intentionally separate from the adapter call: writes occur only while constructing the synthetic test image. The production adapter receives the completed image and performs read-only listing.

## Assertions

The test calls the existing `sleuthkit_fls(image_path)` function rather than invoking `fls` directly for the assertion under certification.

Acceptance requires the live `fls` output to contain the filesystem entry `nexus-evidence.txt`. The test additionally checks that the host-side temporary source path is not leaked into the filesystem listing.

No subprocess result from `fls` is mocked.

## CI controls

The workflow runs on Ubuntu 24.04 with Python 3.12. It installs `sleuthkit` and `e2fsprogs` from the runner's configured Ubuntu package repositories and prints the installed tool versions before certification.

Before the E2E test, Python compiles the integration package. The E2E suite is guarded by `NEXUS_RUN_SLEUTHKIT_E2E=1`, so ordinary unit-test discovery does not require the external forensic binary.

## Security and evidence boundary

This certification performs offline analysis of a locally generated synthetic disk image. It does not access a physical disk, external host, cloud account, network target, or real person's data. It performs no exploitation, persistence, credential acquisition, tracking, interception, or remote collection.

## Acceptance gate

This slice is accepted only when the repository's normal `quality` workflow remains green and the `certify-sleuthkit` job in `forensics-foundation-e2e` completes successfully on the PR head.

Until that happens, this audit documents implementation and review only and does not claim successful live certification.

## Residual risks

- This slice certifies `fls` recursive filesystem listing only; it does not certify every Sleuth Kit executable or filesystem format.
- Ubuntu package repository availability remains an external CI dependency.
- Production evidence handling still requires separate controls for acquisition authorization, write blockers, chain of custody, storage, access control, retention, and examiner procedures.
- Corrupt-media behavior, very large images, partition-offset discovery, encrypted filesystems, deleted-file recovery, and performance are outside this certification slice.
