from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path
import sqlite3
from typing import Any


@dataclass(frozen=True, slots=True)
class ParsedEmail:
    subject: str | None
    from_address: str | None
    to_address: str | None
    date: str | None
    message_id: str | None
    body_text: str


def parse_email_bytes(data: bytes) -> ParsedEmail:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    message = BytesParser(policy=policy.default).parsebytes(data)
    body = message.get_body(preferencelist=("plain",))
    body_text = body.get_content() if body is not None else ""
    return ParsedEmail(
        subject=message.get("Subject"),
        from_address=message.get("From"),
        to_address=message.get("To"),
        date=message.get("Date"),
        message_id=message.get("Message-ID"),
        body_text=body_text,
    )


def sqlite_read_only_query(path: str | Path, sql: str, parameters: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    target = Path(path)
    if not target.is_file():
        raise ValueError("path must reference an existing SQLite file")
    if not sql.lstrip().casefold().startswith(("select", "pragma")):
        raise ValueError("only SELECT or PRAGMA queries are permitted")
    uri = f"file:{target.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        cursor = connection.execute(sql, parameters)
        return list(cursor.fetchall())
    finally:
        connection.close()
