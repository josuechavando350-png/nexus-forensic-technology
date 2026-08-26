from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from packages.integrations import (
    KafkaProducerAdapter,
    Neo4jAdapter,
    OPAAdapter,
    OpenCTIAdapter,
    OpenSearchAdapter,
    PassiveInfrastructureAdapter,
    PostGISAdapter,
    SparkAdapter,
    Web3Adapter,
    parse_email_bytes,
    sqlite_read_only_query,
)


class _FakeResult(list):
    pass


class _FakeSession:
    def __init__(self, rows, calls):
        self.rows = rows
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, query, parameters):
        self.calls.append((query, parameters))
        return _FakeResult(self.rows)


class _FakeDriver:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def session(self, database=None):
        self.database = database
        return _FakeSession(self.rows, self.calls)


class _FakeCursor:
    def __init__(self, row=(123.4,), rows=None):
        self.row = row
        self.rows = rows or []
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class _HTTP:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, *args, **kwargs):
        self.calls.append(("get", args, kwargs))
        return self.response

    def post(self, *args, **kwargs):
        self.calls.append(("post", args, kwargs))
        return self.response


class _SearchClient:
    def __init__(self):
        self.index_calls = []
        self.search_calls = []

    def index(self, **kwargs):
        self.index_calls.append(kwargs)
        return {"result": "created"}

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"hits": {"hits": [{"_id": "1", "_score": 2.0, "_source": {"x": 1}}]}}


class _Producer:
    def __init__(self):
        self.calls = []

    def send(self, topic, key, value):
        self.calls.append((topic, key, value))
        return "future"


class _Spark:
    def __init__(self):
        self.calls = []

    def createDataFrame(self, records):
        self.calls.append(records)
        return ("df", records)


class _Eth:
    def get_transaction(self, value):
        return {"hash": value}

    def get_transaction_receipt(self, value):
        return {"transactionHash": value}

    def get_balance(self, address, block_identifier="latest"):
        return 42


class _Web3:
    eth = _Eth()

    def to_checksum_address(self, address):
        return address.upper()


class IntegrationTests(unittest.TestCase):
    def test_neo4j_uses_parameters_and_safe_relation_type(self):
        driver = _FakeDriver([{"id": "b", "relation": "LINK"}])
        adapter = Neo4jAdapter(driver)
        rows = adapter.neighbors(entity_id="a", relation="LINK", limit=5)
        self.assertEqual(rows[0]["id"], "b")
        query, params = driver.calls[0]
        self.assertIn("$entity_id", query)
        self.assertEqual(params, {"entity_id": "a", "limit": 5})
        with self.assertRaises(ValueError):
            adapter.neighbors(entity_id="a", relation="LINK]-() MATCH (n) //")

    def test_postgis_distance_parameter_order(self):
        cursor = _FakeCursor(row=(1000.25,))
        adapter = PostGISAdapter(_FakeConnection(cursor))
        self.assertEqual(adapter.distance_m(lat1=10, lon1=20, lat2=11, lon2=21), 1000.25)
        _, params = cursor.calls[0]
        self.assertEqual(params, (20, 10, 21, 11))

    def test_opensearch_builds_ranked_query(self):
        client = _SearchClient()
        adapter = OpenSearchAdapter(client, "evidence")
        adapter.index_document(document_id="ev-1", document={"text": "hello"})
        hits = adapter.search_text(query="hello", fields=("text",), size=10)
        self.assertEqual(hits, [{"id": "1", "score": 2.0, "source": {"x": 1}}])
        body = client.search_calls[0]["body"]
        self.assertEqual(body["query"]["multi_match"]["fields"], ["text"])
        self.assertEqual(body["sort"][1], {"_id": "asc"})

    def test_opencti_rejects_graphql_errors(self):
        client = _HTTP(_Response({"errors": [{"message": "bad"}]}))
        adapter = OpenCTIAdapter(client, "https://cti/graphql", "token")
        with self.assertRaises(RuntimeError):
            adapter.graphql(query="query { x }")

    def test_opa_requires_result(self):
        good = OPAAdapter(_HTTP(_Response({"result": {"allow": True}})), "http://opa:8181")
        self.assertEqual(good.evaluate(policy_path="nexus/authz", input_document={"a": 1}), {"allow": True})
        bad = OPAAdapter(_HTTP(_Response({})), "http://opa:8181")
        with self.assertRaises(RuntimeError):
            bad.evaluate(policy_path="nexus/authz", input_document={})

    def test_passive_infrastructure_rdap_and_bgp(self):
        client = _HTTP(_Response({"handle": "example"}))
        adapter = PassiveInfrastructureAdapter(client)
        self.assertEqual(adapter.rdap_domain("Example.COM")["handle"], "example")
        self.assertIn("/example.com", client.calls[0][1][0])
        parsed = adapter.parse_bgp_records([
            {"prefix": "203.0.113.0/24", "origin": "AS64500"},
            {"prefix": "203.0.113.0/24", "origin": "AS64501"},
            {"prefix": "", "origin": "AS1"},
        ])
        self.assertEqual(parsed["203.0.113.0/24"], ("AS64500", "AS64501"))

    def test_email_parser_extracts_headers_and_plain_body(self):
        raw = (
            b"From: a@example.com\r\n"
            b"To: b@example.com\r\n"
            b"Subject: Test\r\n"
            b"Message-ID: <1@example.com>\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"hello\r\n"
        )
        parsed = parse_email_bytes(raw)
        self.assertEqual(parsed.subject, "Test")
        self.assertIn("hello", parsed.body_text)

    def test_sqlite_query_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "db.sqlite"
            con = sqlite3.connect(path)
            con.execute("CREATE TABLE t (x INTEGER)")
            con.execute("INSERT INTO t VALUES (1)")
            con.commit()
            con.close()
            self.assertEqual(sqlite_read_only_query(path, "SELECT x FROM t"), [(1,)])
            with self.assertRaises(ValueError):
                sqlite_read_only_query(path, "DELETE FROM t")

    def test_kafka_serialization_is_deterministic(self):
        producer = _Producer()
        adapter = KafkaProducerAdapter(producer)
        self.assertEqual(adapter.send_json(topic="evidence", key="ev-1", payload={"b": 2, "a": 1}), "future")
        _, _, value = producer.calls[0]
        self.assertEqual(value, b'{"a":1,"b":2}')

    def test_spark_adapter_requires_records(self):
        spark = _Spark()
        adapter = SparkAdapter(spark)
        self.assertEqual(adapter.dataframe_from_records([{"x": 1}])[0], "df")
        with self.assertRaises(ValueError):
            adapter.dataframe_from_records([])

    def test_web3_adapter_delegates_read_only_queries(self):
        adapter = Web3Adapter(_Web3())
        self.assertEqual(adapter.transaction("0xabc")["hash"], "0xabc")
        self.assertEqual(adapter.receipt("0xabc")["transactionHash"], "0xabc")
        self.assertEqual(adapter.balance("0xabc"), 42)


if __name__ == "__main__":
    unittest.main()
