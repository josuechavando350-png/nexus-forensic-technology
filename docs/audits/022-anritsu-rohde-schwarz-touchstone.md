# Audit 022 — Anritsu / Rohde & Schwarz Touchstone evidence

## Scope

Real offline forensic parsing of Touchstone network-parameter files exported by vector network analyzers, including instruments from Anritsu and Rohde & Schwarz. The implementation consumes an existing local file only. It does not connect to an instrument, configure RF settings, initiate sweeps, transmit RF, or acquire live measurements.

## Specification basis

The parser is aligned to the IBIS Open Forum Touchstone File Format Specification Version 2.1 and deliberately implements a bounded subset:

- Touchstone 1.0/1.1 SnP files inferred from the `.sNp` extension.
- Touchstone 2.0/2.1 keyword files with explicit `[Version]`, `[Number of Ports]`, `[Number of Frequencies]`, `[Network Data]`, and `[End]` requirements.
- S, Y, and Z parameters for supported port counts; G and H parameters only for two-port networks.
- RI, MA, and DB network-data encodings.
- Full matrices only. Lower/Upper matrices, noise blocks, mixed-mode blocks, and information blocks fail closed.
- Standard Version 1.x two-port order `N11, N21, N12, N22` and explicit Version 2.x `12_21` / `21_12` order.
- Row-major ordering for Full matrices with three or more ports.
- Single or per-port positive reference impedances where represented by supported syntax.

## Corrections made during audit

The first implementation was not certified as-is. Review against the current specification found and corrected several issues before merge:

1. Option-line parameters were initially treated as positional. The specification permits option-line tokens to appear in different orders, so parsing was changed to recognize units, parameter type, format, and the `R` clause semantically.
2. Version 2.x required-keyword semantics were tightened. The parser now requires the Version 2.x keyword set used by the supported subset and rejects non-comment content after `[End]`.
3. `[Version]` is accepted only for 2.0/2.1 keyword files and must precede other non-comment content.
4. `[Two-Port Data Order]` is required for Version 2.x two-port data and rejected for other port counts.
5. Version 1.1 per-port reference syntax is distinguished from Version 1.0 single-reference syntax for returned metadata.
6. Network frequencies and values must be finite; NaN/Infinity evidence fails closed.
7. Port count is bounded to 64 and local evidence size to 64 MiB.

## Evidence-integrity behavior

- Frequencies must be non-negative and strictly increasing.
- Every frequency block must contain exactly the expected Full matrix value count.
- Declared `[Number of Frequencies]` must match decoded data.
- File-extension port count and `[Number of Ports]` must agree when both exist.
- Reference impedances must be finite and positive.
- Unsupported or ambiguous Touchstone constructs are rejected rather than guessed.

## Tests

`packages/forensic_core/tests/test_touchstone.py` covers:

- Version 1.0 two-port RI data and legacy ordering.
- Order-independent option-line parsing.
- Version 1.1 per-port references.
- Version 2.1 explicit references and alternate two-port ordering.
- Three-port Full row-major ordering.
- Port-count mismatch and unsupported sparse matrices.
- Missing Version 2.x required keywords and incorrect Version placement.
- Incomplete, duplicate-frequency, and non-finite network data.
- G/H two-port restriction.
- Bounded local evidence loading.

## Certification gate

Merge only after final diff review and successful completion of all repository pull-request checks.