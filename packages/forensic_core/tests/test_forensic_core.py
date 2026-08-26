from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
import unittest

from packages.forensic_core import (
    AuthorizationScope,
    ChainOfCustody,
    Edge,
    EvidenceGraph,
    ForensicEvent,
    GeoPoint,
    SourceAssessment,
    Timeline,
    Transaction,
    account_net_flow,
    aggregate_flows,
    authorize,
    bayesian_update,
    compare_identity_text,
    deterministic_report_bytes,
    haversine_distance_m,
    is_candidate_match,
    normalize_competing_hypotheses,
    report_sha256,
    weighted_likelihood,
    within_radius,
)


class ForensicCoreTests(unittest.TestCase):
    def test_chain_of_custody_is_hash_linked_and_detects_tampering(self) -> None:
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        chain = ChainOfCustody()
        first = chain.append(evidence_id="ev-1", actor="analyst-a", action="acquired", timestamp=t0)
        second = chain.append(evidence_id="ev-1", actor="analyst-b", action="verified", timestamp=t0 + timedelta(minutes=2))
        self.assertEqual(second.previous_hash, first.event_hash)
        self.assertTrue(chain.verify())
        tampered = type(second)(evidence_id=second.evidence_id, actor=second.actor, action="changed", timestamp=second.timestamp, previous_hash=second.previous_hash, event_hash=second.event_hash)
        with self.assertRaisesRegex(ValueError, "invalid custody chain"):
            ChainOfCustody((first, tampered))

    def test_timeline_orders_deterministically_and_filters(self) -> None:
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        events = [
            ForensicEvent("b", t0, "src-1", "file", "B"),
            ForensicEvent("a", t0, "src-2", "file", "A"),
            ForensicEvent("c", t0 + timedelta(seconds=1), "src-3", "file", "C"),
        ]
        timeline = Timeline(events)
        self.assertEqual([event.event_id for event in timeline.ordered()], ["a", "b", "c"])
        self.assertEqual([event.event_id for event in timeline.between(t0, t0)], ["a", "b"])

    def test_graph_path_and_components_are_stable(self) -> None:
        graph = EvidenceGraph()
        graph.add_edge(Edge("a", "b", "related"))
        graph.add_edge(Edge("b", "c", "related"))
        graph.add_edge(Edge("x", "y", "related"))
        self.assertEqual(graph.shortest_path("a", "c"), ("a", "b", "c"))
        self.assertEqual(graph.connected_components(), (("a", "b", "c"), ("x", "y")))

    def test_identity_matching_is_transparent_and_conservative(self) -> None:
        exact = compare_identity_text("José Pérez", "jose perez")
        self.assertEqual(exact.score, 1.0)
        self.assertEqual(exact.method, "normalized-exact")
        self.assertTrue(is_candidate_match(exact))
        weak = compare_identity_text("alice", "bob")
        self.assertLess(weak.score, 0.90)
        self.assertFalse(is_candidate_match(weak))

    def test_bayesian_and_source_weighting_are_valid(self) -> None:
        posterior = bayesian_update(prior=0.5, likelihood_if_true=0.9, likelihood_if_false=0.1)
        self.assertAlmostEqual(posterior, 0.9)
        assessment = SourceAssessment(reliability=0.5, information_credibility=0.5)
        self.assertAlmostEqual(weighted_likelihood(raw_likelihood=0.9, assessment=assessment), 0.6)
        self.assertEqual(normalize_competing_hypotheses({"h1": 3.0, "h2": 1.0}), {"h1": 0.75, "h2": 0.25})

    def test_policy_fails_closed_for_out_of_scope_or_expired_requests(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        scope = AuthorizationScope(case_id="case-1", purposes=frozenset({"forensic-review"}), source_types=frozenset({"provided-file"}), actions=frozenset({"analyze"}), valid_until=now + timedelta(hours=1))
        self.assertTrue(authorize(scope, purpose="forensic-review", source_type="provided-file", action="analyze", at=now).allowed)
        self.assertFalse(authorize(scope, purpose="other", source_type="provided-file", action="analyze", at=now).allowed)
        self.assertFalse(authorize(scope, purpose="forensic-review", source_type="provided-file", action="analyze", at=now + timedelta(hours=2)).allowed)

    def test_geospatial_distance_and_radius(self) -> None:
        a = GeoPoint(19.4326, -99.1332)
        b = GeoPoint(19.4270, -99.1677)
        distance = haversine_distance_m(a, b)
        self.assertGreater(distance, 3_000)
        self.assertLess(distance, 5_000)
        self.assertTrue(within_radius(a, a, 0))
        with self.assertRaises(ValueError):
            within_radius(a, b, -1)

    def test_financial_flow_uses_decimal_and_rejects_duplicates(self) -> None:
        txs = [Transaction("t1", "a", "b", Decimal("10.10"), "MXN"), Transaction("t2", "a", "b", Decimal("0.20"), "mxn")]
        self.assertEqual(aggregate_flows(txs), {("a", "b", "MXN"): Decimal("10.30")})
        self.assertEqual(account_net_flow(txs, "a", "MXN"), Decimal("-10.30"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            aggregate_flows([txs[0], txs[0]])

    def test_report_bytes_are_deterministic_and_strict_json(self) -> None:
        first = {"b": 2, "a": "á"}
        second = {"a": "á", "b": 2}
        self.assertEqual(deterministic_report_bytes(first), deterministic_report_bytes(second))
        self.assertEqual(report_sha256(first), report_sha256(second))
        with self.assertRaises(ValueError):
            deterministic_report_bytes({"bad": math.nan})


if __name__ == "__main__":
    unittest.main()
