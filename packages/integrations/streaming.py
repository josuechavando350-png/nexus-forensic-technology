from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping


@dataclass(slots=True)
class KafkaProducerAdapter:
    producer: Any

    def send_json(self, *, topic: str, key: str, payload: Mapping[str, Any]) -> Any:
        if not topic.strip() or not key.strip():
            raise ValueError("topic and key must not be blank")
        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return self.producer.send(topic, key=key.encode("utf-8"), value=encoded)


@dataclass(slots=True)
class SparkAdapter:
    spark: Any

    def dataframe_from_records(self, records: list[Mapping[str, Any]]) -> Any:
        if not records:
            raise ValueError("records must not be empty")
        return self.spark.createDataFrame([dict(record) for record in records])
