from __future__ import annotations

import os
import time
import unittest
from typing import Any, Callable

from packages.integrations.geospatial import PostGISAdapter
from packages.integrations.graph import Neo4jAdapter
from packages.integrations.search import OpenSearchAdapter


def _wait_until(check: Callable[[], bool], *, timeout_s: float = 90.0, interval_s: float = 1.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except Exception as exc:  # readiness polling must retain the last service error
            last_error = exc
        time.sleep(interval_s)
    raise RuntimeError(f"service did not become ready within {timeout_s:.0f}s") from last_error


class DataFoundationE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("NEXUS_RUN_DATA_FOUNDATION_E2E") != "1":
            raise unittest.SkipTest("live data-foundation dependencies are only required in the dedicated E2E workflow")

        try:
            import psycopg
            from neo4j import GraphDatabase
            from opensearchpy import OpenSearch
        except ImportError as exc:
            raise RuntimeError("data-foundation E2E client dependencies are not installed") from exc

        cls.psycopg: Any = psycopg
        cls.GraphDatabase: Any = GraphDatabase
        cls.OpenSearch: Any = OpenSearch
        cls.pg_dsn = os.environ.get(
            "NEXUS_POSTGIS_DSN",
            "postgresql://nexus:nexus@127.0.0.1:5432/nexus",
        )
        cls.neo4j_uri = os.environ.get("NEXUS_NEO4J_URI", "bolt://127.0.0.1:7687")
        cls.neo4j_user = os.environ.get("NEXUS_NEO4J_USER", "neo4j")
        cls.neo4j_password = os.environ.get("NEXUS_NEO4J_PASSWORD", "nexusforensic")
        cls.opensearch_url = os.environ.get("NEXUS_OPENSEARCH_URL", "http://127.0.0.1:9200")

        _wait_until(cls._postgis_ready)
        _wait_until(cls._neo4j_ready)
        _wait_until(cls._opensearch_ready)

    @classmethod
    def _postgis_ready(cls) -> bool:
        with cls.psycopg.connect(cls.pg_dsn, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)

    @classmethod
    def _neo4j_ready(cls) -> bool:
        driver = cls.GraphDatabase.driver(
            cls.neo4j_uri,
            auth=(cls.neo4j_user, cls.neo4j_password),
            connection_timeout=3,
        )
        try:
            driver.verify_connectivity()
            return True
        finally:
            driver.close()

    @classmethod
    def _opensearch_ready(cls) -> bool:
        client = cls.OpenSearch(cls.opensearch_url, timeout=3)
        return bool(client.ping())

    def test_postgis_adapter_against_real_postgis(self) -> None:
        with self.psycopg.connect(self.pg_dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                cursor.execute("DROP TABLE IF EXISTS nexus_e2e_points")
                cursor.execute(
                    "CREATE TABLE nexus_e2e_points (id text PRIMARY KEY, geom geometry(Point, 4326) NOT NULL)"
                )
                cursor.execute(
                    "INSERT INTO nexus_e2e_points (id, geom) VALUES "
                    "(%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)), "
                    "(%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
                    ("near", -99.1332, 19.4326, "far", -100.3161, 25.6866),
                )
            connection.commit()

            adapter = PostGISAdapter(connection)
            distance = adapter.distance_m(
                lat1=19.4326,
                lon1=-99.1332,
                lat2=19.4326,
                lon2=-99.1332,
            )
            self.assertAlmostEqual(distance, 0.0, places=6)

            rows = adapter.points_within_radius(
                table="nexus_e2e_points",
                geom_column="geom",
                latitude=19.4326,
                longitude=-99.1332,
                radius_m=5_000,
            )
            self.assertEqual([row[0] for row in rows], ["near"])

    def test_neo4j_adapter_against_real_neo4j(self) -> None:
        driver = self.GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password),
        )
        try:
            with driver.session() as session:
                session.run("MATCH (n:NexusE2E) DETACH DELETE n").consume()
                session.run(
                    "CREATE (a:NexusE2E {id: 'A'}), (b:NexusE2E {id: 'B'}), (c:NexusE2E {id: 'C'}), "
                    "(a)-[:LINK]->(b), (b)-[:LINK]->(c)"
                ).consume()

            adapter = Neo4jAdapter(driver)
            neighbors = adapter.neighbors(entity_id="A", relation="LINK")
            self.assertEqual(neighbors, [{"id": "B", "relation": "LINK"}])
            self.assertEqual(adapter.shortest_path(source_id="A", target_id="C"), ["A", "B", "C"])
        finally:
            driver.close()

    def test_opensearch_adapter_against_real_opensearch(self) -> None:
        client = self.OpenSearch(self.opensearch_url, timeout=10)
        index = "nexus-e2e-evidence"
        if client.indices.exists(index=index):
            client.indices.delete(index=index)
        client.indices.create(index=index)
        try:
            adapter = OpenSearchAdapter(client=client, index=index)
            adapter.index_document(
                document_id="evidence-001",
                document={"title": "forensic evidence", "body": "chain of custody verified"},
            )
            client.indices.refresh(index=index)
            hits = adapter.search_text(query="custody", fields=("title", "body"))
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["id"], "evidence-001")
            self.assertEqual(hits[0]["source"]["body"], "chain of custody verified")
        finally:
            client.indices.delete(index=index, ignore=[404])


if __name__ == "__main__":
    unittest.main()
