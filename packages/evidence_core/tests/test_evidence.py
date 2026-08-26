import unittest
from dataclasses import FrozenInstanceError

from packages.evidence_core.evidence import EvidenceRecord, create_evidence_record, sha256_hex, verify_evidence_bytes


class EvidenceIntegrityTests(unittest.TestCase):
    def test_known_sha256_vector(self) -> None:
        self.assertEqual(sha256_hex(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_empty_bytes_vector(self) -> None:
        self.assertEqual(sha256_hex(b""), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_record_captures_hash_and_size(self) -> None:
        record = create_evidence_record(evidence_id="EV-0001", source_ref="case://CASE-001/source/original.bin", data=b"sample")
        self.assertEqual(record.size_bytes, 6)
        self.assertEqual(record.sha256_hex, sha256_hex(b"sample"))

    def test_record_is_immutable(self) -> None:
        record = create_evidence_record(evidence_id="EV-0001", source_ref="case://CASE-001/source/original.bin", data=b"sample")
        with self.assertRaises(FrozenInstanceError):
            record.size_bytes = 7

    def test_blank_identifiers_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_evidence_record(evidence_id=" ", source_ref="case://CASE-001/source/original.bin", data=b"sample")
        with self.assertRaises(ValueError):
            create_evidence_record(evidence_id="EV-0001", source_ref=" ", data=b"sample")

    def test_original_bytes_verify(self) -> None:
        data = b"sample"
        record = create_evidence_record(evidence_id="EV-0001", source_ref="case://CASE-001/source/original.bin", data=data)
        self.assertTrue(verify_evidence_bytes(record, data))

    def test_tampering_fails_verification(self) -> None:
        record = create_evidence_record(evidence_id="EV-0001", source_ref="case://CASE-001/source/original.bin", data=b"abc")
        self.assertFalse(verify_evidence_bytes(record, b"abd"))

    def test_invalid_record_fields_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceRecord(evidence_id="EV-0001", source_ref="case://CASE-001/source/original.bin", sha256_hex="00", size_bytes=2)
        with self.assertRaises(ValueError):
            EvidenceRecord(evidence_id="EV-0001", source_ref="case://CASE-001/source/original.bin", sha256_hex="0" * 64, size_bytes=-1)


if __name__ == "__main__":
    unittest.main()
