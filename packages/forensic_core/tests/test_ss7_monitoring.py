from __future__ import annotations

import csv
import io
import unittest

from packages.forensic_core.ss7_monitoring import (
    SS7MonitoringError,
    analyze_ss7_records,
    parse_tshark_ss7_fields,
    tshark_ss7_argv,
)


def _row(*fields: str) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="")
    writer.writerow(fields)
    return output.getvalue()


class SS7MonitoringTests(unittest.TestCase):
    def test_parses_real_wireshark_field_schema(self) -> None:
        text = _row(
            "10",
            "1788312000.125000",
            "1234",
            "5678",
            "3",
            "5215512345678",
            "5215587654321",
            "0x62",
            "01:02:03:04",
            "",
            "44",
            "",
        )
        records = parse_tshark_ss7_fields(text)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.opc, 1234)
        self.assertEqual(record.dpc, 5678)
        self.assertEqual(record.service_indicator, 3)
        self.assertEqual(record.tcap_message_type, 0x62)
        self.assertEqual(record.otid, "01020304")
        self.assertEqual(record.operation_code, 44)

    def test_correlates_begin_continue_end_transaction_ids(self) -> None:
        text = "\n".join(
            (
                _row("1", "1.0", "1", "2", "3", "111", "222", "0x62", "aa", "", "1", ""),
                _row("2", "2.0", "2", "1", "3", "222", "111", "0x65", "bb", "aa", "", ""),
                _row("3", "3.0", "1", "2", "3", "111", "222", "0x64", "", "bb", "", ""),
            )
        )
        report = analyze_ss7_records(parse_tshark_ss7_fields(text))
        self.assertEqual(report.record_count, 3)
        self.assertEqual(report.tcap_transactions_started, 1)
        self.assertEqual(report.findings, ())

    def test_flags_transaction_integrity_and_tcap_errors(self) -> None:
        text = "\n".join(
            (
                _row("1", "1.0", "1", "2", "3", "", "", "0x62", "aa", "", "", ""),
                _row("2", "2.0", "1", "2", "3", "", "", "0x62", "aa", "", "", ""),
                _row("3", "3.0", "2", "1", "3", "", "", "0x64", "", "ff", "", "7"),
            )
        )
        report = analyze_ss7_records(parse_tshark_ss7_fields(text))
        codes = [finding.code for finding in report.findings]
        self.assertIn("duplicate_begin_otid", codes)
        self.assertIn("unmatched_dtid", codes)
        self.assertIn("tcap_error", codes)
        self.assertEqual(report.tcap_errors, 1)

    def test_flags_m3ua_service_mismatch(self) -> None:
        records = parse_tshark_ss7_fields(
            _row("1", "1.0", "1", "2", "5", "111", "222", "", "", "", "", "")
        )
        report = analyze_ss7_records(records)
        self.assertEqual(report.findings[0].code, "m3ua_service_mismatch")

    def test_rejects_invalid_transaction_identifier(self) -> None:
        with self.assertRaisesRegex(SS7MonitoringError, "invalid OTID"):
            parse_tshark_ss7_fields(
                _row("1", "1.0", "1", "2", "3", "", "", "0x62", "xyz", "", "", "")
            )

    def test_command_is_offline_only_and_uses_verified_fields(self) -> None:
        argv = tshark_ss7_argv("evidence.pcapng", "/usr/bin/tshark")
        self.assertEqual(argv[:3], ("/usr/bin/tshark", "-r", "evidence.pcapng"))
        self.assertNotIn("-i", argv)
        self.assertIn("m3ua.protocol_data_opc", argv)
        self.assertIn("sccp.calling.digits", argv)
        self.assertIn("tcap.otid", argv)
        self.assertIn("tcap.opCode", argv)
        self.assertIn("separator=/t", argv)


if __name__ == "__main__":
    unittest.main()
