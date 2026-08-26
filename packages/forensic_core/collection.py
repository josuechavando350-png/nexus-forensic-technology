from __future__ import annotations

from dataclasses import dataclass
import heapq


@dataclass(frozen=True, slots=True)
class CollectionTask:
    task_id: str
    priority: int
    rationale: str

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.rationale.strip():
            raise ValueError("task_id and rationale must not be blank")


class CollectionQueue:
    def __init__(self) -> None:
        self._heap: list[tuple[int, str, CollectionTask]] = []
        self._ids: set[str] = set()

    def add(self, task: CollectionTask) -> None:
        if task.task_id in self._ids:
            raise ValueError(f"duplicate task_id: {task.task_id}")
        self._ids.add(task.task_id)
        heapq.heappush(self._heap, (-task.priority, task.task_id, task))

    def pop_next(self) -> CollectionTask:
        if not self._heap:
            raise IndexError("collection queue is empty")
        _, task_id, task = heapq.heappop(self._heap)
        self._ids.remove(task_id)
        return task

    def __len__(self) -> int:
        return len(self._heap)
