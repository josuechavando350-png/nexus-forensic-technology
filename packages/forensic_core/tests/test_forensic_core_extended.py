from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from packages.forensic_core import (
    BM25Index,
    CaseIndicator,
    CaseRecord,
    CaseStore,
    CollectionQueue,
    CollectionTask,
    Indicator,
    PackageEntry,
    build_package_manifest,
    detect_basic_contact_data,
    hash_file_read_only,
    linked_case_pairs,
    manifest_bytes,
    merkle_root_hex,
    normalize_domain,
    normalize_ip,
    normalize_url,
    redact_ranges,
    shared_indicators,
    z_scores,
)


class ForensicCoreExtendedTests(unittest.TestCase):
    def test_merkle_root_is_deterministic_and_order_sensitive(self) -> None:
        first = merkle_root_hex([b"a", b"b", b"c"])
        second = merkle_root_hex([b"a", b"b", b"c"])
        changed = merkle_root_hex([b"b", b"a", b"c"])
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertEqual(len(first), 64)

    def test_case_store_enforces_case_and_evidence_uniqueness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore(Path(directory) / "cases.sqlite3")
            case = CaseRecord("case-1", "Test case", datetime(2026, 1, 1, tzinfo=timezone.utc))
            store.create_case(case)
            with self.assertRaisesRegex(ValueError, "already exists"):
                store.create_case(case)
            store.attach_evidence(case_id="case-1", evidence_id="ev-2")
            store.attach_evidence(case_id="case-1", evidence_id="ev-1")
            self.assertEqual(store.evidence_ids("case-1"), ("ev-1", "ev-2"))
            with self.assertRaises(ValueError):
                store.attach_evidence(case_id="missing", evidence_id="ev-3")

    def test_indicator_normalization(self) -> None:
        self.assertEqual(normalize_ip("2001:0db8::1"), "2001:db8::1")
        self.assertEqual(normalize_domain("Example.COM."), "example.com")
        self.assertEqual(normalize_url("HTTPS://Example.COM:443/path#fragment"), "https://example.com/path")
        self.assertEqual(Indicator.parse("DOMAIN", "Example.COM").value, "example.com")
        with self.assertRaises(ValueError):
            normalize_url("ftp://example.com/file")

    def test_cross_case_correlation_requires_shared_indicator(self) -> None:
        records = [
            CaseIndicator("case-a", "domain:example.com"),
            CaseIndicator("case-b", "domain:example.com"),
            CaseIndicator("case-b", "ip:192.0.2.1"),
            CaseIndicator("case-c", "ip:192.0.2.1"),
            CaseIndicator("case-a", "unique"),
        ]
        self.assertEqual(shared_indicators(records), {"domain:example.com": ("case-a", "case-b"), "ip:192.0.2.1": ("case-b", "case-c")})
        self.assertEqual(linked_case_pairs(records), {("case-a", "case-b"): ("domain:example.com",), ("case-b", "case-c"): ("ip:192.0.2.1",)})

    def test_read_only_acquisition_hashes_exact_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.bin"
            path.write_bytes(b"abc")
            record = hash_file_read_only(path, chunk_size=1)
            self.assertEqual(record.size_bytes, 3)
            self.assertEqual(record.sha256_hex, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            self.assertEqual(path.read_bytes(), b"abc")

    def test_z_scores_handle_constant_series_without_division_by_zero(self) -> None:
        results = z_scores([5, 5, 5])
        self.assertEqual(tuple(result.z_score for result in results), (0.0, 0.0, 0.0))

    def test_collection_queue_is_priority_then_id_deterministic(self) -> None:
        queue = CollectionQueue()
        queue.add(CollectionTask("b", 10, "reason-b"))
        queue.add(CollectionTask("a", 10, "reason-a"))
        queue.add(CollectionTask("c", 5, "reason-c"))
        self.assertEqual(queue.pop_next().task_id, "a")
        self.assertEqual(queue.pop_next().task_id, "b")
        self.assertEqual(queue.pop_next().task_id, "c")
        with self.assertRaises(IndexError):
            queue.pop_next()

    def test_basic_privacy_redaction_uses_explicit_ranges(self) -> None:
        text = "Mail a.person@example.com or call +52 555 123 4567."
        findings = detect_basic_contact_data(text)
        kinds = {finding.kind for finding in findings}
        self.assertEqual(kinds, {"email", "phone"})
        redacted = redact_ranges(text, findings)
        self.assertNotIn("a.person@example.com", redacted)
        self.assertNotIn("555 123 4567", redacted)
        with self.assertRaises(ValueError):
            redact_ranges("abc", [type(findings[0])(1, 3, "x"), type(findings[0])(2, 3, "y")])

    def test_package_manifest_is_deterministic_and_rejects_traversal(self) -> None:
        entries = build_package_manifest({"b.txt": b"b", "a.txt": b"a"})
        self.assertEqual([entry.path for entry in entries], ["a.txt", "b.txt"])
        self.assertEqual(manifest_bytes(entries), manifest_bytes(tuple(reversed(entries))))
        with self.assertRaises(ValueError):
            PackageEntry("../escape", 1, "0" * 64)

    def test_bm25_search_is_ranked_and_deterministic(self) -> None:
        index = BM25Index({"doc-b": "forensic evidence timeline", "doc-a": "forensic evidence evidence", "doc-c": "unrelated content"})
        hits = index.search("forensic evidence")
        self.assertGreater(hits[0].score, 0)
        self.assertEqual(hits[0].document_id, "doc-a")
        self.assertEqual([hit.document_id for hit in index.search("missing")], [])


if __name__ == "__main__":
    unittest.main()
