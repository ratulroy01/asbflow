import json

import pytest

from asbflow import ASBPublisher, PublishError, PublishExecutionMode
from asbflow.config import ASBMessagingEntity, ASBPublisherConfig
from asbflow.config.message import (
    ASBDynamicMessageConfig,
    ASBMessageConfig,
    MessageFieldMapping,
)


def test_service_publish_message_and_publish_batch(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
        execution_mode=PublishExecutionMode.SEQUENTIAL,
    )

    publisher.publish_message(base_payload)
    publisher.publish_batch([base_payload, payload_2], chunk_size=1)

    assert len(factory.client.sender.sent) == 3


def test_service_publish_auto_routes_single_and_batch(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
        execution_mode="thread_pool",
    )

    publisher.publish(base_payload)
    publisher.publish([base_payload, payload_2], chunk_size=2)

    assert len(factory.client.sender.sent) == 2
    assert json.loads(factory.client.sender.sent[0].body_arg)["id"] == "msg-1"


def test_service_publish_with_async_strategy_mode(
    patch_async_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_async_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
        execution_mode="async",
    )

    publisher.publish([base_payload, payload_2], chunk_size=1)

    assert len(factory.client.sender.sent) == 2


def test_service_publish_with_alert_message_model(
    patch_publisher_sdk,
    alert_message,
    connection_config,
    publisher_config,
    message_config,
):
    factory = patch_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    publisher.publish(alert_message)

    sent = factory.client.sender.sent[0]
    payload = json.loads(sent.body_arg)
    assert payload["id"] == alert_message.id


def test_service_publish_with_async_strategy_inside_running_loop(
    patch_async_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_async_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
        execution_mode="async",
    )

    async def _runner() -> None:
        publisher.publish([base_payload, payload_2], chunk_size=1)

    import asyncio

    asyncio.run(_runner())

    assert len(factory.client.sender.sent) == 2


def test_service_publish_raises_on_error(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
    alert_message_parser,
):
    patch_publisher_sdk()
    invalid_payload = dict(base_payload)
    invalid_payload.pop("alert")

    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
        parser=alert_message_parser,
    )

    with pytest.raises(PublishError) as exc_info:
        publisher.publish_parsed(invalid_payload)

    assert exc_info.value.operation == "publish"


def test_service_exposes_configuration(
    connection_config,
    publisher_config,
    message_config,
):
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
        execution_mode="thread_pool",
    )

    assert publisher.connection_config is connection_config
    assert publisher.publisher_config is publisher_config
    assert publisher.message_config is message_config
    assert publisher.execution_mode is PublishExecutionMode.THREAD_POOL


def test_service_publish_uses_queue_sender_when_configured(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    message_config,
):
    queue_publisher_config = ASBPublisherConfig(
        entity_type=ASBMessagingEntity.QUEUE,
        queue_name="queue-a",
    )
    factory = patch_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=queue_publisher_config,
        message=message_config,
    )

    publisher.publish_message(base_payload)

    assert factory.client.sender_method == "queue"
    assert factory.client.sender_kwargs is not None
    assert factory.client.sender_kwargs["queue_name"] == "queue-a"


def test_service_publish_message_allows_message_config_override(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    factory = patch_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    override = ASBMessageConfig(message_id="override-id", subject="override-subject")
    publisher.publish_message(base_payload, message=override)

    sent = factory.client.sender.sent[0]
    assert sent.kwargs["message_id"] == "override-id"
    assert sent.kwargs["subject"] == "override-subject"


def test_service_publish_batch_allows_dynamic_message_config(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
):
    payload_1 = dict(base_payload)
    payload_1["id"] = "msg-1"
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_publisher_sdk()
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=ASBMessageConfig(),
    )

    dynamic_message = ASBDynamicMessageConfig(
        message_id=MessageFieldMapping(lambda message: message["id"] if isinstance(message, dict) else None),
        subject=MessageFieldMapping(lambda message: message["alert"]["name"] if isinstance(message, dict) else None),
    )

    publisher.publish_batch([payload_1, payload_2], chunk_size=1, message=dynamic_message)

    first_batch_messages = factory.client.sender.sent[0].messages
    second_batch_messages = factory.client.sender.sent[1].messages
    assert first_batch_messages[0].kwargs["message_id"] == "msg-1"
    assert second_batch_messages[0].kwargs["message_id"] == "msg-2"
    assert first_batch_messages[0].kwargs["subject"] == "Test alert"
