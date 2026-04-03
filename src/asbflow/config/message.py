from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Generic, TypeAlias, TypeVar

from asbflow.shared.payloads import PublishablePayload

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class MessageFieldMapping(Generic[T]):
    """Resolve a message config field from the payload being published."""

    extractor: Callable[[PublishablePayload], T | None]

    def resolve(self, payload: PublishablePayload) -> T | None:
        return self.extractor(payload)


@dataclass(frozen=True, slots=True)
class ASBMessageConfig:
    content_type: str | None = "application/json"
    message_id: str | None = None
    correlation_id: str | None = None
    subject: str | None = None
    partition_key: str | None = None
    session_id: str | None = None
    time_to_live: timedelta | None = None
    scheduled_enqueue_time_utc: datetime | None = None
    to: str | None = None
    reply_to: str | None = None
    reply_to_session_id: str | None = None
    application_properties: dict[str, Any] | None = None
    message_kwargs: dict[str, Any] = field(default_factory=dict)

    def to_message_kwargs(self) -> dict[str, Any]:
        source: dict[str, Any] = asdict(self)

        extra_kwargs: dict[str, Any] = source.pop("message_kwargs")

        kwargs: dict[str, Any] = {k: v for k, v in source.items() if v is not None}
        kwargs.update(extra_kwargs)
        return kwargs


@dataclass(frozen=True, slots=True)
class ASBDynamicMessageConfig:
    """Message config that supports per-payload dynamic value extraction."""

    content_type: str | MessageFieldMapping[str] | None = "application/json"
    message_id: str | MessageFieldMapping[str] | None = None
    correlation_id: str | MessageFieldMapping[str] | None = None
    subject: str | MessageFieldMapping[str] | None = None
    partition_key: str | MessageFieldMapping[str] | None = None
    session_id: str | MessageFieldMapping[str] | None = None
    time_to_live: timedelta | MessageFieldMapping[timedelta] | None = None
    scheduled_enqueue_time_utc: datetime | MessageFieldMapping[datetime] | None = None
    to: str | MessageFieldMapping[str] | None = None
    reply_to: str | MessageFieldMapping[str] | None = None
    reply_to_session_id: str | MessageFieldMapping[str] | None = None
    application_properties: dict[str, Any] | MessageFieldMapping[dict[str, Any]] | None = None
    message_kwargs: dict[str, Any] | MessageFieldMapping[dict[str, Any]] = field(default_factory=dict)

    @staticmethod
    def _resolve_field(value: T | MessageFieldMapping[T] | None, payload: PublishablePayload) -> T | None:
        if isinstance(value, MessageFieldMapping):
            return value.resolve(payload)
        return value

    def to_message_config(self, payload: PublishablePayload) -> ASBMessageConfig:
        resolve_field_partial: Callable = partial(self._resolve_field, payload=payload)
        return ASBMessageConfig(
            content_type=resolve_field_partial(self.content_type),
            message_id=resolve_field_partial(self.message_id),
            correlation_id=resolve_field_partial(self.correlation_id),
            subject=resolve_field_partial(self.subject),
            partition_key=resolve_field_partial(self.partition_key),
            session_id=resolve_field_partial(self.session_id),
            time_to_live=resolve_field_partial(self.time_to_live),
            scheduled_enqueue_time_utc=resolve_field_partial(self.scheduled_enqueue_time_utc),
            to=resolve_field_partial(self.to),
            reply_to=resolve_field_partial(self.reply_to),
            reply_to_session_id=resolve_field_partial(self.reply_to_session_id),
            application_properties=resolve_field_partial(self.application_properties),
            message_kwargs=resolve_field_partial(self.message_kwargs) or {},
        )


MessageConfigInput: TypeAlias = ASBMessageConfig | ASBDynamicMessageConfig


__all__ = ["ASBMessageConfig", "ASBDynamicMessageConfig", "MessageFieldMapping", "MessageConfigInput"]
