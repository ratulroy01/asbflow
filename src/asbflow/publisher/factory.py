from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from asbflow.auth import ASBClientProviderFactory
from asbflow.auth.base import ASBClientProvider
from asbflow.config import ASBConnectionConfig, ASBMessageConfig, ASBPublisherConfig
from asbflow.shared.parsing import PydanticModelParser

from .base import BasePublisherStrategy
from .strategies import (
    AsyncPublisherStrategy,
    SequentialPublisherStrategy,
    ThreadPoolPublisherStrategy,
)

if TYPE_CHECKING:
    from .service import ASBPublisher


class PublishExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    THREAD_POOL = "thread_pool"
    ASYNC = "async"

    @classmethod
    def parse(cls, value: "PublishExecutionMode | str") -> "PublishExecutionMode":
        if isinstance(value, cls):
            return value

        normalized: str = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases: dict[str, PublishExecutionMode] = {
            "serial": cls.SEQUENTIAL,
            "sequential": cls.SEQUENTIAL,
            "threadpool": cls.THREAD_POOL,
            "thread_pool": cls.THREAD_POOL,
            "threadpooled": cls.THREAD_POOL,
            "thread_pooled": cls.THREAD_POOL,
            "async": cls.ASYNC,
            "asyncio": cls.ASYNC,
            "async_concurrent": cls.ASYNC,
        }

        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unknown publish execution mode: {value}. " "Supported values are sequential, thread_pool, async."
            ) from exc


class PublisherFactory:
    """Build publisher strategies and services."""

    @staticmethod
    def create_strategy(
        mode: PublishExecutionMode | str,
        *,
        connection: ASBConnectionConfig,
        publisher: ASBPublisherConfig,
        message: ASBMessageConfig | None = None,
        parser: PydanticModelParser | None = None,
    ) -> BasePublisherStrategy:
        parsed_mode: PublishExecutionMode = PublishExecutionMode.parse(mode)
        client_provider: ASBClientProvider = ASBClientProviderFactory.create(connection)

        match parsed_mode:
            case PublishExecutionMode.SEQUENTIAL:
                return SequentialPublisherStrategy(
                    connection,
                    publisher,
                    message,
                    parser,
                    client_provider=client_provider,
                )
            case PublishExecutionMode.THREAD_POOL:
                return ThreadPoolPublisherStrategy(
                    connection,
                    publisher,
                    message,
                    parser,
                    client_provider=client_provider,
                )
            case PublishExecutionMode.ASYNC:
                return AsyncPublisherStrategy(
                    connection,
                    publisher,
                    message,
                    parser,
                    client_provider=client_provider,
                )
            case _:
                raise ValueError(f"Unknown publish execution mode: {parsed_mode}")

    @staticmethod
    def create_service(
        connection: ASBConnectionConfig,
        publisher: ASBPublisherConfig,
        *,
        message: ASBMessageConfig | None = None,
        execution_mode: PublishExecutionMode | str = PublishExecutionMode.SEQUENTIAL,
        parser: PydanticModelParser | None = None,
    ) -> ASBPublisher:
        from .service import ASBPublisher

        strategy: BasePublisherStrategy = PublisherFactory.create_strategy(
            execution_mode,
            connection=connection,
            publisher=publisher,
            message=message,
            parser=parser,
        )
        return ASBPublisher(
            connection=connection,
            publisher=publisher,
            message=message,
            execution_mode=execution_mode,
            parser=parser,
            strategy=strategy,
        )


def create_publisher(
    connection: ASBConnectionConfig,
    publisher: ASBPublisherConfig,
    *,
    message: ASBMessageConfig | None = None,
    execution_mode: PublishExecutionMode | str = PublishExecutionMode.SEQUENTIAL,
    parser: PydanticModelParser | None = None,
) -> ASBPublisher:
    """Create an ``ASBPublisher`` service with configured auth and strategy."""
    return PublisherFactory.create_service(
        connection=connection,
        publisher=publisher,
        message=message,
        execution_mode=execution_mode,
        parser=parser,
    )


__all__ = [
    "PublishExecutionMode",
    "PublisherFactory",
    "create_publisher",
]
