import asyncio

import pytest

from asbflow.config.message import ASBDynamicMessageConfig, MessageFieldMapping
from asbflow.publisher.strategies import (
    AsyncPublisherStrategy,
    SequentialPublisherStrategy,
    ThreadPoolPublisherStrategy,
)


@pytest.mark.parametrize(
    "strategy_cls",
    [SequentialPublisherStrategy, ThreadPoolPublisherStrategy],
)
def test_sync_strategies_publish_batch_send_all_messages(
    strategy_cls,
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_publisher_sdk()
    strategy = strategy_cls(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish_batch([base_payload, payload_2], chunk_size=1)

    assert len(factory.client.sender.sent) == 2


def test_sync_strategy_uses_max_batch_size_when_chunk_none(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"
    payload_3 = dict(base_payload)
    payload_3["id"] = "msg-3"

    factory = patch_publisher_sdk(max_batch_size=2)
    strategy = SequentialPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish_batch([base_payload, payload_2, payload_3])

    assert len(factory.client.sender.sent) == 2
    assert len(factory.client.sender.sent[0].messages) == 2
    assert len(factory.client.sender.sent[1].messages) == 1


def test_async_strategy_publish_batch_uses_async_sdk(
    patch_async_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_async_publisher_sdk()
    strategy = AsyncPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish_batch([base_payload, payload_2], chunk_size=1)

    assert len(factory.client.sender.sent) == 2


def test_async_strategy_publish_batch_inside_running_loop(
    patch_async_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    factory = patch_async_publisher_sdk()
    strategy = AsyncPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    async def _runner() -> None:
        strategy.publish_batch([base_payload, payload_2], chunk_size=1)

    asyncio.run(_runner())

    assert len(factory.client.sender.sent) == 2


def test_sync_strategy_invalid_chunk_size_raises(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    patch_publisher_sdk()
    strategy = ThreadPoolPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    with pytest.raises(ValueError, match="chunk_size must be a positive integer"):
        strategy.publish_batch([base_payload], chunk_size=0)


@pytest.mark.parametrize(
    "strategy_cls",
    [SequentialPublisherStrategy, ThreadPoolPublisherStrategy],
)
def test_sync_strategies_chunk_size_still_respects_batch_size_limit(
    strategy_cls,
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"
    payload_3 = dict(base_payload)
    payload_3["id"] = "msg-3"

    factory = patch_publisher_sdk(max_batch_size=2)
    strategy = strategy_cls(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish_batch([base_payload, payload_2, payload_3], chunk_size=100)

    assert len(factory.client.sender.sent) == 2
    assert len(factory.client.sender.sent[0].messages) == 2
    assert len(factory.client.sender.sent[1].messages) == 1


def test_async_strategy_chunk_size_still_respects_batch_size_limit(
    patch_async_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"
    payload_3 = dict(base_payload)
    payload_3["id"] = "msg-3"

    factory = patch_async_publisher_sdk(max_batch_size=2)
    strategy = AsyncPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish_batch([base_payload, payload_2, payload_3], chunk_size=100)

    assert len(factory.client.sender.sent) == 2
    assert len(factory.client.sender.sent[0].messages) == 2
    assert len(factory.client.sender.sent[1].messages) == 1


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture",
    [
        (SequentialPublisherStrategy, "patch_publisher_sdk"),
        (ThreadPoolPublisherStrategy, "patch_publisher_sdk"),
        (AsyncPublisherStrategy, "patch_async_publisher_sdk"),
    ],
)
def test_strategies_support_dynamic_message_config(
    request,
    strategy_cls,
    patch_fixture,
    base_payload,
    connection_config,
    publisher_config,
):
    payload_1 = dict(base_payload)
    payload_1["id"] = "msg-1"
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    patch = request.getfixturevalue(patch_fixture)
    factory = patch()
    strategy = strategy_cls(
        connection=connection_config,
        publisher=publisher_config,
    )

    dynamic_message = ASBDynamicMessageConfig(
        message_id=MessageFieldMapping(lambda message: message["id"] if isinstance(message, dict) else None),
    )

    strategy.publish_batch([payload_1, payload_2], chunk_size=1, message=dynamic_message)

    first_sent = factory.client.sender.sent[0]
    second_sent = factory.client.sender.sent[1]

    if hasattr(first_sent, "messages"):
        first_message = first_sent.messages[0]
        second_message = second_sent.messages[0]
    else:
        first_message = first_sent
        second_message = second_sent

    assert first_message.kwargs["message_id"] == "msg-1"
    assert second_message.kwargs["message_id"] == "msg-2"
