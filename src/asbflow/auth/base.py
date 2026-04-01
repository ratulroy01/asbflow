from __future__ import annotations

from abc import ABC, abstractmethod

from asbflow.config.connection import ASBConnectionConfig
from asbflow.shared.sdk import ASBAsyncClient, ASBSyncClient


class ASBClientProvider(ABC):
    """Base abstraction for Azure Service Bus client providers."""

    def __init__(self, config: ASBConnectionConfig) -> None:
        """Initialize the provider.

        Parameters
        ----------
        config : ASBConnectionConfig
            Connection/auth configuration used to create clients.
        """
        self._config: ASBConnectionConfig = config

    @property
    def config(self) -> ASBConnectionConfig:
        """Return the connection configuration used by this provider."""
        return self._config

    @abstractmethod
    def create_sync_client(self) -> ASBSyncClient:
        """Create a synchronous Azure Service Bus client.

        Returns
        -------
        ASBSyncClient
            Sync client implementing context manager semantics.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_async_client(self) -> ASBAsyncClient:
        """Create an asynchronous Azure Service Bus client.

        Returns
        -------
        ASBAsyncClient
            Async client implementing async context manager semantics.
        """
        raise NotImplementedError


__all__ = ["ASBClientProvider"]
