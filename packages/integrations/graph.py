from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be blank")
    return value.strip()


@dataclass(slots=True)
class Neo4jAdapter:
    driver: Any
    database: str | None = None

    def _execute(self, query: str, parameters: Mapping[str, Any]) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            result = session.run(query, dict(parameters))
            return [dict(record) for record in result]

    def neighbors(self, *, entity_id: str, relation: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        entity_id = _nonblank(entity_id, "entity_id")
        if limit <= 0 or limit > 10_000:
            raise ValueError("limit must be between 1 and 10000")
        if relation is None:
            query = """
                MATCH (a {id: $entity_id})-[r]-(b)
                RETURN b.id AS id, type(r) AS relation
                ORDER BY id, relation
                LIMIT $limit
            """
            params = {"entity_id": entity_id, "limit": limit}
        else:
            relation = _nonblank(relation, "relation")
            if not relation.replace("_", "").isalnum():
                raise ValueError("relation must contain only letters, numbers, or underscores")
            query = f"""
                MATCH (a {{id: $entity_id}})-[r:{relation}]-(b)
                RETURN b.id AS id, type(r) AS relation
                ORDER BY id, relation
                LIMIT $limit
            """
            params = {"entity_id": entity_id, "limit": limit}
        return self._execute(query, params)

    def shortest_path(self, *, source_id: str, target_id: str, max_depth: int = 6) -> list[str] | None:
        source_id = _nonblank(source_id, "source_id")
        target_id = _nonblank(target_id, "target_id")
        if not 1 <= max_depth <= 12:
            raise ValueError("max_depth must be between 1 and 12")
        query = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            MATCH p = shortestPath((a)-[*..{max_depth}]-(b))
            RETURN [n IN nodes(p) | n.id] AS path
        """
        rows = self._execute(query, {"source_id": source_id, "target_id": target_id})
        return list(rows[0]["path"]) if rows else None


@dataclass(slots=True)
class NetworkXAdapter:
    graph: Any

    def shortest_path(self, source: str, target: str) -> tuple[str, ...] | None:
        try:
            import networkx as nx
        except ImportError as exc:
            raise RuntimeError("networkx is required for NetworkXAdapter") from exc
        try:
            return tuple(nx.shortest_path(self.graph, source=source, target=target))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def connected_components(self) -> tuple[tuple[str, ...], ...]:
        try:
            import networkx as nx
        except ImportError as exc:
            raise RuntimeError("networkx is required for NetworkXAdapter") from exc
        components = [tuple(sorted(component)) for component in nx.connected_components(self.graph)]
        return tuple(sorted(components))
