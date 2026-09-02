# Audit 021 — SS7/SIGTRAN monitoring

## Scope

Real offline SS7/SIGTRAN evidence analysis built on Wireshark/TShark display fields. The module reads an existing PCAP/PCAPNG file with `tshark -r`; it does not open a capture interface, transmit signaling, inject messages, query a carrier network, or perform subscriber interception.

## Verified protocol fields

The decoder uses Wireshark display fields that are present in the current 4.6 display-filter reference:

- `m3ua.protocol_data_opc`
- `m3ua.protocol_data_dpc`
- `m3ua.protocol_data_si`
- `sccp.calling.digits`
- `sccp.called.digits`
- `tcap.msgtype`
- `tcap.otid`
- `tcap.dtid`
- `tcap.opCode`
- `tcap.errorCode`

Frame number and epoch timestamp are included for evidentiary correlation.

## Implementation checks

- TShark command is offline-only: it always supplies `-r <capture>` and never supplies `-i`.
- Field output uses TShark's documented `-T fields`, `-E separator=/t`, double quoting, and first-occurrence controls.
- Frame metadata, integer protocol fields, and transaction identifiers are strictly validated.
- TCAP transaction correlation distinguishes Begin (`0x62`), Continue (`0x65`), End (`0x64`), and Abort (`0x67`).
- Begin OTID collisions, responses without DTIDs, unmatched DTIDs, TCAP errors, invalid M3UA service indicators, and decoded SCCP/TCAP with a non-SCCP M3UA service indicator are surfaced as deterministic findings.
- Findings are structural/integrity observations only; no unsupported attribution or surveillance conclusion is generated.
- Process timeouts and non-zero TShark results fail explicitly.

## Tests

`packages/forensic_core/tests/test_ss7_monitoring.py` covers the verified field schema, quoted tab-separated parsing, normal Begin/Continue/End correlation, duplicate transaction identifiers, unmatched destination identifiers, TCAP error reporting, service-indicator mismatch, malformed transaction IDs, and exact offline command construction.

## Certification gate

Merge only after final diff review and successful completion of all repository pull-request checks.
