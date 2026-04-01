from __future__ import annotations

from typing import Protocol, runtime_checkable

from asbflow.consumer.result import ConsumeResult
from asbflow.shared.parsing import PydanticModelParser
from asbflow.shared.payloads import PublishInput


@runtime_checkable
class _ConsumerLike(Protocol):
    def consume(
        self,
        max_message_count: int,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool | None = None,
        settle_messages: bool = True,
    ) -> ConsumeResult: ...

    def read(
        self,
        max_message_count: int,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool | None = None,
    ) -> ConsumeResult: ...


@runtime_checkable
class _PublisherLike(Protocol):
    def publish(
        self,
        payload: PublishInput,
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None: ...


__all__ = ["_ConsumerLike", "_PublisherLike"]
