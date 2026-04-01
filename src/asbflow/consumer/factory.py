from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from asbflow.auth import ASBClientProviderFactory
from asbflow.config import ASBConnectionConfig, ASBConsumerConfig
from asbflow.shared.parsing import PydanticModelParser

from .base import BaseConsumerStrategy
from .strategies import (
    AsyncConsumerStrategy,
    SequentialConsumerStrategy,
    ThreadPoolConsumerStrategy,
)

if TYPE_CHECKING:
    from .service import ASBConsumer


class ConsumeExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    THREAD_POOL = "thread_pool"
    ASYNC = "async"

    @classmethod
    def parse(cls, value: "ConsumeExecutionMode | str") -> "ConsumeExecutionMode":
        if isinstance(value, cls):
            return value

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "serial": cls.SEQUENTIAL,
            "sequential": cls.SEQUENTIAL,
            "threadpool": cls.THREAD_POOL,
            "thread_pool": cls.THREAD_POOL,
            "threadpooled": cls.THREAD_POOL,
            "thread_pooled": cls.THREAD_POOL,
            "async": cls.ASYNC,
            "asyncio": cls.ASYNC,
        }

        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unknown consume execution mode: {value}. " "Supported values are sequential, thread_pool, async."
            ) from exc


class ConsumerFactory:
    """Build consumer strategies and services."""

    @staticmethod
    def create_strategy(
        mode: ConsumeExecutionMode | str,
        *,
        connection: ASBConnectionConfig,
        consumer: ASBConsumerConfig,
        parser: PydanticModelParser | None = None,
    ) -> BaseConsumerStrategy:
        parsed_mode = ConsumeExecutionMode.parse(mode)
        client_provider = ASBClientProviderFactory.create(connection)

        if parsed_mode is ConsumeExecutionMode.SEQUENTIAL:
            return SequentialConsumerStrategy(
                connection,
                consumer,
                parser,
                client_provider=client_provider,
            )
        if parsed_mode is ConsumeExecutionMode.THREAD_POOL:
            return ThreadPoolConsumerStrategy(
                connection,
                consumer,
                parser,
                client_provider=client_provider,
            )
        return AsyncConsumerStrategy(
            connection,
            consumer,
            parser,
            client_provider=client_provider,
        )

    @staticmethod
    def create_service(
        connection: ASBConnectionConfig,
        consumer: ASBConsumerConfig,
        *,
        execution_mode: ConsumeExecutionMode | str = ConsumeExecutionMode.SEQUENTIAL,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool = True,
    ) -> ASBConsumer:
        from .service import ASBConsumer

        strategy = ConsumerFactory.create_strategy(
            execution_mode,
            connection=connection,
            consumer=consumer,
            parser=parser,
        )
        return ASBConsumer(
            connection=connection,
            consumer=consumer,
            execution_mode=execution_mode,
            parser=parser,
            raise_on_error=raise_on_error,
            strategy=strategy,
        )


def create_consumer(
    connection: ASBConnectionConfig,
    consumer: ASBConsumerConfig,
    *,
    execution_mode: ConsumeExecutionMode | str = ConsumeExecutionMode.SEQUENTIAL,
    parser: PydanticModelParser | None = None,
    raise_on_error: bool = True,
) -> ASBConsumer:
    """Create an ``ASBConsumer`` service with configured auth and strategy."""
    return ConsumerFactory.create_service(
        connection=connection,
        consumer=consumer,
        execution_mode=execution_mode,
        parser=parser,
        raise_on_error=raise_on_error,
    )


__all__ = [
    "ConsumeExecutionMode",
    "ConsumerFactory",
    "create_consumer",
]
