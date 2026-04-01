from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from asbflow.config import ASBConsumerConfig, ASBPublisherConfig
from asbflow.shared.sdk import ASBAsyncClient, ASBSyncClient


class ASBEntityClient(ABC):
    """Resolve sender/receiver objects for a specific ASB entity kind."""

    @abstractmethod
    def get_sync_sender(self, client: ASBSyncClient, publisher: ASBPublisherConfig) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_async_sender(
        self,
        client: ASBAsyncClient,
        publisher: ASBPublisherConfig,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_sync_receiver(self, client: ASBSyncClient, consumer: ASBConsumerConfig) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_async_receiver(
        self,
        client: ASBAsyncClient,
        consumer: ASBConsumerConfig,
    ) -> Any:
        raise NotImplementedError


__all__ = ["ASBEntityClient"]
