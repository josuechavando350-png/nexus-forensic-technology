from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CaseRecord:
    case_id: str
    title: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be blank")
        if not self.title.strip():
            raise ValueError("title must not be blank")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")


class CaseStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS case_evidence (
                    case_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    PRIMARY KEY (case_id, evidence_id),
                    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
                )
            """)

    def create_case(self, case: CaseRecord) -> None:
        timestamp = case.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connect() as connection:
            try:
                connection.execute("INSERT INTO cases (case_id, title, created_at) VALUES (?, ?, ?)", (case.case_id, case.title, timestamp))
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"case already exists: {case.case_id}") from exc

    def attach_evidence(self, *, case_id: str, evidence_id: str) -> None:
        if not evidence_id.strip():
            raise ValueError("evidence_id must not be blank")
        with self._connect() as connection:
            try:
                connection.execute("INSERT INTO case_evidence (case_id, evidence_id) VALUES (?, ?)", (case_id, evidence_id))
            except sqlite3.IntegrityError as exc:
                raise ValueError("case missing or evidence already attached") from exc

    def evidence_ids(self, case_id: str) -> tuple[str, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT evidence_id FROM case_evidence WHERE case_id = ? ORDER BY evidence_id", (case_id,)).fetchall()
        return tuple(row["evidence_id"] for row in rows)
