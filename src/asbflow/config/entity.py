from __future__ import annotations

from enum import Enum


class ASBMessagingEntity(str, Enum):
    TOPIC = "topic"
    QUEUE = "queue"

    @classmethod
    def parse(cls, value: ASBMessagingEntity | str) -> ASBMessagingEntity:
        if isinstance(value, cls):
            return value

        normalized: str = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases: dict[str, ASBMessagingEntity] = {
            "topic": cls.TOPIC,
            "topics": cls.TOPIC,
            "queue": cls.QUEUE,
            "queues": cls.QUEUE,
        }
        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(f"Unknown messaging entity type: {value}. Supported values are topic and queue.") from exc


__all__ = ["ASBMessagingEntity"]
