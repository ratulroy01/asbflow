from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from asbflow.config.entity import ASBMessagingEntity


class ParseFailurePolicy(str, Enum):
    # Move invalid payloads to dead-letter queue (recommended default).
    DEAD_LETTER = "dead_letter"
    # Mark invalid payloads as consumed and remove them from the queue.
    COMPLETE = "complete"
    # Release invalid payloads back to the queue for redelivery.
    ABANDON = "abandon"
    # Leave invalid payloads unsettled (can cause re-delivery loops).
    LEAVE_UNSETTLED = "leave_unsettled"


@dataclass(frozen=True, slots=True)
class ASBConsumerConfig:
    entity_type: ASBMessagingEntity | str = ASBMessagingEntity.TOPIC
    topic_name: str | None = None
    subscription_name: str | None = None
    queue_name: str | None = None
    max_wait_time: float | None = None
    receive_mode: Any | None = None
    sub_queue: Any | None = None
    prefetch_count: int | None = None
    client_identifier: str | None = None
    socket_timeout: float | None = None
    parse_failure_policy: ParseFailurePolicy | str = ParseFailurePolicy.DEAD_LETTER
    receiver_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        resolved_entity: ASBMessagingEntity = ASBMessagingEntity.parse(self.entity_type)
        object.__setattr__(self, "entity_type", resolved_entity)

        if resolved_entity is ASBMessagingEntity.TOPIC:
            if not self.topic_name:
                raise ValueError("topic_name is required when entity_type='topic'")
            if not self.subscription_name:
                raise ValueError("subscription_name is required when entity_type='topic'")
            return

        if not self.queue_name:
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

    def to_receiver_kwargs(self) -> dict[str, Any]:
        source: dict[str, Any] = asdict(self)

        extra_kwargs: dict[str, Any] = source.pop("receiver_kwargs")
        source.pop("parse_failure_policy")
        source.pop("entity_type")

        kwargs: dict[str, Any] = {k: v for k, v in source.items() if v is not None}

        if self.entity is ASBMessagingEntity.TOPIC:
            kwargs.pop("queue_name", None)
            kwargs["topic_name"] = self.entity_name
            if not self.subscription_name:
                raise ValueError("subscription_name is required when entity_type='topic'")
            kwargs["subscription_name"] = self.subscription_name
        else:
            kwargs.pop("topic_name", None)
            kwargs.pop("subscription_name", None)
            kwargs["queue_name"] = self.entity_name

        kwargs.update(extra_kwargs)
        return kwargs

    @property
    def resolved_parse_failure_policy(self) -> ParseFailurePolicy:
        value = self.parse_failure_policy
        if isinstance(value, ParseFailurePolicy):
            return value

        normalized: str = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "dead_letter": ParseFailurePolicy.DEAD_LETTER,
            "deadletter": ParseFailurePolicy.DEAD_LETTER,
            "complete": ParseFailurePolicy.COMPLETE,
            "abandon": ParseFailurePolicy.ABANDON,
            "leave_unsettled": ParseFailurePolicy.LEAVE_UNSETTLED,
            "leave": ParseFailurePolicy.LEAVE_UNSETTLED,
        }
        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unknown parse failure policy: {value}. "
                "Supported values are dead_letter, complete, abandon, leave_unsettled."
            ) from exc


__all__ = ["ASBConsumerConfig", "ParseFailurePolicy"]
