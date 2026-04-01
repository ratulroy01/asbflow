from __future__ import annotations

from typing import Any

from asbflow.config import ASBConsumerConfig, ASBPublisherConfig
from asbflow.entity.base import ASBEntityClient
from asbflow.shared.sdk import ASBAsyncClient, ASBSyncClient


class TopicEntityClient(ASBEntityClient):
    def get_sync_sender(self, client: ASBSyncClient, publisher: ASBPublisherConfig) -> Any:
        return client.get_topic_sender(**publisher.to_sender_kwargs())

    def get_async_sender(
        self,
        client: ASBAsyncClient,
        publisher: ASBPublisherConfig,
    ) -> Any:
        return client.get_topic_sender(**publisher.to_sender_kwargs())

    def get_sync_receiver(self, client: ASBSyncClient, consumer: ASBConsumerConfig) -> Any:
        return client.get_subscription_receiver(**consumer.to_receiver_kwargs())

    def get_async_receiver(
        self,
        client: ASBAsyncClient,
        consumer: ASBConsumerConfig,
    ) -> Any:
        return client.get_subscription_receiver(**consumer.to_receiver_kwargs())


class QueueEntityClient(ASBEntityClient):
    def get_sync_sender(self, client: ASBSyncClient, publisher: ASBPublisherConfig) -> Any:
        return client.get_queue_sender(**publisher.to_sender_kwargs())

    def get_async_sender(
        self,
        client: ASBAsyncClient,
        publisher: ASBPublisherConfig,
    ) -> Any:
        return client.get_queue_sender(**publisher.to_sender_kwargs())

    def get_sync_receiver(self, client: ASBSyncClient, consumer: ASBConsumerConfig) -> Any:
        return client.get_queue_receiver(**consumer.to_receiver_kwargs())

    def get_async_receiver(
        self,
        client: ASBAsyncClient,
        consumer: ASBConsumerConfig,
    ) -> Any:
        return client.get_queue_receiver(**consumer.to_receiver_kwargs())


__all__ = ["TopicEntityClient", "QueueEntityClient"]
