from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from asbflow.config.entity import ASBMessagingEntity


@dataclass(frozen=True, slots=True)
class ASBPublisherConfig:
    topic_name: str | None = None
    queue_name: str | None = None
    entity_type: ASBMessagingEntity | str = ASBMessagingEntity.TOPIC
    client_identifier: str | None = None
    socket_timeout: float | None = None
    sender_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        resolved_entity: ASBMessagingEntity = ASBMessagingEntity.parse(self.entity_type)
        object.__setattr__(self, "entity_type", resolved_entity)

        if resolved_entity is ASBMessagingEntity.TOPIC and not self.topic_name:
            raise ValueError("topic_name is required when entity_type='topic'")

        if resolved_entity is ASBMessagingEntity.QUEUE and not self.queue_name:
            raise ValueError("queue_name is required when entity_type='queue'")

    @property
    def entity(self) -> ASBMessagingEntity:
        value = self.entity_type
        if isinstance(value, ASBMessagingEntity):
            return value
        return ASBMessagingEntity.parse(value)

    @property
    def entity_name(self) -> str:
        if self.entity is ASBMessagingEntity.TOPIC:
            if not self.topic_name:
                raise ValueError("topic_name is required when entity_type='topic'")
            return self.topic_name

        if not self.queue_name:
            raise ValueError("queue_name is required when entity_type='queue'")
        return self.queue_name

    def to_sender_kwargs(self) -> dict[str, Any]:
        source: dict[str, Any] = asdict(self)
        extra_kwargs: dict[str, Any] = source.pop("sender_kwargs")
        source.pop("entity_type")

        kwargs: dict[str, Any] = {k: v for k, v in source.items() if v is not None}

        if self.entity is ASBMessagingEntity.TOPIC:
            kwargs.pop("queue_name", None)
            kwargs["topic_name"] = self.entity_name
        else:
            kwargs.pop("topic_name", None)
            kwargs["queue_name"] = self.entity_name

        kwargs.update(extra_kwargs)
        return kwargs


__all__ = ["ASBPublisherConfig"]
