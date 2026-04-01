from __future__ import annotations

from asbflow.config import ASBConsumerConfig, ASBMessagingEntity, ASBPublisherConfig
from asbflow.entity.base import ASBEntityClient
from asbflow.entity.providers import QueueEntityClient, TopicEntityClient


class ASBEntityClientFactory:
    """Build entity handlers for publisher/consumer configurations."""

    @staticmethod
    def create_for_publisher(config: ASBPublisherConfig) -> ASBEntityClient:
        match config.entity:
            case ASBMessagingEntity.TOPIC:
                return TopicEntityClient()
            case ASBMessagingEntity.QUEUE:
                return QueueEntityClient()
            case _:
                raise ValueError(f"Unsupported publisher entity type: {config.entity}")

    @staticmethod
    def create_for_consumer(config: ASBConsumerConfig) -> ASBEntityClient:
        match config.entity:
            case ASBMessagingEntity.TOPIC:
                return TopicEntityClient()
            case ASBMessagingEntity.QUEUE:
                return QueueEntityClient()
            case _:
                raise ValueError(f"Unsupported consumer entity type: {config.entity}")


__all__ = ["ASBEntityClientFactory"]
