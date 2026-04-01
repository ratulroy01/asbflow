from __future__ import annotations

from dataclasses import replace
from typing import Any

from asbflow.config import (
    ASBConnectionConfig,
    ASBConsumerConfig,
    ASBPublisherConfig,
    get_asbflow_logger,
)
from asbflow.consumer import ASBConsumer, create_consumer
from asbflow.dlq.protocols import _ConsumerLike, _PublisherLike
from asbflow.dlq.service import ASBDLQManager
from asbflow.publisher import ASBPublisher, create_publisher
from asbflow.shared.parsing import PydanticModelParser
from asbflow.shared.sdk import load_asb_dead_letter_subqueue

LOGGER = get_asbflow_logger(__name__)


def _resolve_dead_letter_sub_queue() -> object:
    try:
        resolved: object = load_asb_dead_letter_subqueue()
        LOGGER.debug("Resolved DLQ sub_queue from azure.servicebus: %r", resolved)
        return resolved
    except Exception as exc:
        LOGGER.warning(
            "Could not resolve ServiceBusSubQueue.DEAD_LETTER; falling back to 'deadletter'. error=%s",
            exc,
            exc_info=True,
        )
        return "deadletter"


def ensure_dlq_consumer_config(consumer: ASBConsumerConfig) -> ASBConsumerConfig:
    """Return a consumer config guaranteed to target the dead-letter subqueue."""
    if consumer.sub_queue is not None:
        return consumer

    dlq_sub_queue: object = _resolve_dead_letter_sub_queue()
    LOGGER.info(
        "Enforcing DLQ sub_queue=%r for consumer config (entity=%s, subscription=%s)",
        dlq_sub_queue,
        consumer.entity_name,
        consumer.subscription_name,
    )
    return replace(consumer, sub_queue=dlq_sub_queue)


def create_dlq_manager(
    connection: ASBConnectionConfig,
    consumer: ASBConsumer | ASBConsumerConfig | _ConsumerLike,
    *,
    publisher: ASBPublisher | ASBPublisherConfig | _PublisherLike | None = None,
    parser: PydanticModelParser | None = None,
    raise_on_error: bool = True,
) -> ASBDLQManager:
    """Build a DLQ manager from services or configs.

    If a consumer config is provided, this factory enforces the DLQ subqueue.
    """
    expected_dlq_sub_queue: object = _resolve_dead_letter_sub_queue()

    consumer_service: ASBConsumer | _ConsumerLike
    if isinstance(consumer, ASBConsumerConfig):
        enforced_consumer = ensure_dlq_consumer_config(consumer)
        consumer_service = create_consumer(
            connection=connection,
            consumer=enforced_consumer,
            parser=parser,
        )
    else:
        consumer_service = consumer

    if isinstance(consumer_service, ASBConsumer):
        actual_sub_queue: Any = consumer_service.consumer_config.sub_queue
        if actual_sub_queue != expected_dlq_sub_queue:
            LOGGER.warning(
                "Consumer may not target DLQ sub_queue (expected=%r, actual=%r)",
                expected_dlq_sub_queue,
                actual_sub_queue,
            )

    publisher_service: ASBPublisher | _PublisherLike | None
    if isinstance(publisher, ASBPublisherConfig):
        publisher_service = create_publisher(
            connection=connection,
            publisher=publisher,
        )
    else:
        publisher_service = publisher

    return ASBDLQManager(
        consumer=consumer_service,
        publisher=publisher_service,
        raise_on_error=raise_on_error,
    )


__all__ = ["create_dlq_manager", "ensure_dlq_consumer_config"]
