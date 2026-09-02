from __future__ import annotations

import csv
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_TSHARK_FIELDS = (
    "frame.number",
    "frame.time_epoch",
    "m3ua.protocol_data_opc",
    "m3ua.protocol_data_dpc",
    "m3ua.protocol_data_si",
    "sccp.calling.digits",
    "sccp.called.digits",
    "tcap.msgtype",
    "tcap.otid",
    "tcap.dtid",
    "tcap.opCode",
    "tcap.errorCode",
)


class SS7MonitoringError(RuntimeError):
    """Raised when offline SS7/SIGTRAN evidence cannot be decoded or validated."""


@dataclass(frozen=True, slots=True)
class SS7Record:
    frame_number: int
    timestamp_epoch: float
    opc: int | None
    dpc: int | None
    service_indicator: int | None
    calling_digits: str | None
    called_digits: str | None
    tcap_message_type: int | None
    otid: str | None
    dtid: str | None
    operation_code: int | None
    error_code: int | None


@dataclass(frozen=True, slots=True)
class SS7Finding:
    frame_number: int
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class SS7MonitoringReport:
    record_count: int
    unique_opcs: tuple[int, ...]
    unique_dpcs: tuple[int, ...]
    tcap_transactions_started: int
    tcap_errors: int
    findings: tuple[SS7Finding, ...]


def tshark_ss7_argv(capture_path: str | Path, executable: str = "tshark") -> tuple[str, ...]:
    """Build a TShark command that reads an existing capture and never captures live traffic."""

    source = str(Path(capture_path))
    argv: list[str] = [
        executable,
        "-r",
        source,
        "-Y",
        "m3ua || sccp || tcap || gsm_map",
        "-T",
        "fields",
        "-E",
        "separator=/t",
        "-E",
        "quote=d",
        "-E",
        "occurrence=f",
    ]
    for field in _TSHARK_FIELDS:
        argv.extend(("-e", field))
    return tuple(argv)


def _parse_optional_int(value: str, *, field: str, line_number: int) -> int | None:
    candidate = value.strip()
    if not candidate:
        return None
    try:
        parsed = int(candidate, 0)
    except ValueError as exc:
        raise SS7MonitoringError(f"line {line_number}: invalid {field}") from exc
    if parsed < 0:
        raise SS7MonitoringError(f"line {line_number}: negative {field}")
    return parsed


def _normalize_tid(value: str, *, field: str, line_number: int) -> str | None:
    candidate = value.strip().lower().replace(":", "").replace(" ", "")
    if not candidate:
        return None
    if len(candidate) % 2 or any(char not in "0123456789abcdef" for char in candidate):
        raise SS7MonitoringError(f"line {line_number}: invalid {field}")
    return candidate


def parse_tshark_ss7_fields(text: str) -> tuple[SS7Record, ...]:
    """Parse quoted tab-separated output from :func:`tshark_ss7_argv`."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    records: list[SS7Record] = []
    for line_number, row in enumerate(csv.reader(text.splitlines(), delimiter="\t", quotechar='"'), start=1):
        if not row or all(not item.strip() for item in row):
            continue
        if len(row) != len(_TSHARK_FIELDS):
            raise SS7MonitoringError(
                f"line {line_number}: expected {len(_TSHARK_FIELDS)} fields, got {len(row)}"
            )
        try:
            frame_number = int(row[0])
            timestamp_epoch = float(row[1])
        except ValueError as exc:
            raise SS7MonitoringError(f"line {line_number}: invalid frame metadata") from exc
        if frame_number <= 0 or timestamp_epoch < 0:
            raise SS7MonitoringError(f"line {line_number}: invalid frame metadata")

        records.append(
            SS7Record(
                frame_number=frame_number,
                timestamp_epoch=timestamp_epoch,
                opc=_parse_optional_int(row[2], field="OPC", line_number=line_number),
                dpc=_parse_optional_int(row[3], field="DPC", line_number=line_number),
                service_indicator=_parse_optional_int(
                    row[4], field="service indicator", line_number=line_number
                ),
                calling_digits=row[5].strip() or None,
                called_digits=row[6].strip() or None,
                tcap_message_type=_parse_optional_int(
                    row[7], field="TCAP message type", line_number=line_number
                ),
                otid=_normalize_tid(row[8], field="OTID", line_number=line_number),
                dtid=_normalize_tid(row[9], field="DTID", line_number=line_number),
                operation_code=_parse_optional_int(
                    row[10], field="TCAP operation code", line_number=line_number
                ),
                error_code=_parse_optional_int(
                    row[11], field="TCAP error code", line_number=line_number
                ),
            )
        )
    return tuple(records)


def analyze_ss7_records(records: tuple[SS7Record, ...] | list[SS7Record]) -> SS7MonitoringReport:
    """Run deterministic integrity checks over decoded SS7/SIGTRAN evidence."""

    findings: list[SS7Finding] = []
    seen_otids: dict[str, int] = {}
    started = 0
    errors = 0

    for record in records:
        if record.service_indicator is not None and not 0 <= record.service_indicator <= 15:
            findings.append(
                SS7Finding(record.frame_number, "invalid_service_indicator", str(record.service_indicator))
            )
        if record.opc is not None and record.opc > 0xFFFFFFFF:
            findings.append(SS7Finding(record.frame_number, "invalid_opc", str(record.opc)))
        if record.dpc is not None and record.dpc > 0xFFFFFFFF:
            findings.append(SS7Finding(record.frame_number, "invalid_dpc", str(record.dpc)))

        if record.otid:
            started += 1
            previous_frame = seen_otids.get(record.otid)
            if previous_frame is not None:
                findings.append(
                    SS7Finding(
                        record.frame_number,
                        "duplicate_otid",
                        f"transaction {record.otid} first seen in frame {previous_frame}",
                    )
                )
            else:
                seen_otids[record.otid] = record.frame_number

        if record.dtid and record.dtid not in seen_otids:
            findings.append(
                SS7Finding(
                    record.frame_number,
                    "unmatched_dtid",
                    f"destination transaction {record.dtid} has no earlier OTID in this evidence set",
                )
            )

        if record.error_code is not None:
            errors += 1
            findings.append(
                SS7Finding(
                    record.frame_number,
                    "tcap_error",
                    f"TCAP error code {record.error_code}",
                )
            )

        has_sccp_or_tcap = any(
            value is not None
            for value in (
                record.calling_digits,
                record.called_digits,
                record.tcap_message_type,
                record.otid,
                record.dtid,
                record.operation_code,
                record.error_code,
            )
        )
        if has_sccp_or_tcap and record.service_indicator is not None and record.service_indicator != 3:
            findings.append(
                SS7Finding(
                    record.frame_number,
                    "m3ua_service_mismatch",
                    f"decoded SCCP/TCAP data with M3UA service indicator {record.service_indicator}",
                )
            )

    return SS7MonitoringReport(
        record_count=len(records),
        unique_opcs=tuple(sorted({record.opc for record in records if record.opc is not None})),
        unique_dpcs=tuple(sorted({record.dpc for record in records if record.dpc is not None})),
        tcap_transactions_started=started,
        tcap_errors=errors,
        findings=tuple(findings),
    )


def analyze_ss7_capture(
    capture_path: str | Path,
    executable: str = "tshark",
    *,
    timeout_seconds: float = 120.0,
) -> SS7MonitoringReport:
    """Decode and analyze an existing PCAP/PCAPNG file without opening a capture interface."""

    source = Path(capture_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    resolved = shutil.which(executable) if "/" not in executable else executable
    if not resolved:
        raise FileNotFoundError(executable)
    try:
        completed = subprocess.run(
            tshark_ss7_argv(source, resolved),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise SS7MonitoringError("TShark SS7 analysis timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "TShark returned a non-zero status"
        raise SS7MonitoringError(detail)
    return analyze_ss7_records(parse_tshark_ss7_fields(completed.stdout))
