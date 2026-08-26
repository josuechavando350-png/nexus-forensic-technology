from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.target.strip() or not self.relation.strip():
            raise ValueError("source, target, and relation must not be blank")


class EvidenceGraph:
    def __init__(self) -> None:
        self._adjacency: dict[str, set[str]] = {}
        self._edges: set[Edge] = set()

    def add_edge(self, edge: Edge, *, bidirectional: bool = True) -> None:
        if not isinstance(edge, Edge):
            raise TypeError("edge must be an Edge")
        self._edges.add(edge)
        self._adjacency.setdefault(edge.source, set()).add(edge.target)
        self._adjacency.setdefault(edge.target, set())
        if bidirectional:
            self._adjacency[edge.target].add(edge.source)

    @property
    def edges(self) -> tuple[Edge, ...]:
        return tuple(sorted(self._edges, key=lambda e: (e.source, e.target, e.relation)))

    def neighbors(self, node: str) -> tuple[str, ...]:
        return tuple(sorted(self._adjacency.get(node, set())))

    def shortest_path(self, source: str, target: str) -> tuple[str, ...] | None:
        if source == target:
            return (source,) if source in self._adjacency else None
        if source not in self._adjacency or target not in self._adjacency:
            return None
        queue = deque([(source, (source,))])
        seen = {source}
        while queue:
            node, path = queue.popleft()
            for neighbor in sorted(self._adjacency[node]):
                if neighbor == target:
                    return path + (neighbor,)
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, path + (neighbor,)))
        return None

    def connected_components(self) -> tuple[tuple[str, ...], ...]:
        remaining = set(self._adjacency)
        components: list[tuple[str, ...]] = []
        while remaining:
            start = min(remaining)
            stack = [start]
            component: set[str] = set()
            while stack:
                node = stack.pop()
                if node in component:
                    continue
                component.add(node)
                stack.extend(self._adjacency[node] - component)
            remaining -= component
            components.append(tuple(sorted(component)))
        return tuple(sorted(components))
