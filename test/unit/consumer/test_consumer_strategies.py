import asyncio
import json

import pytest

from asbflow.config import ASBConsumerConfig
from asbflow.consumer.strategies import (
    AsyncConsumerStrategy,
    SequentialConsumerStrategy,
    ThreadPoolConsumerStrategy,
)


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture",
    [
        (SequentialConsumerStrategy, "patch_consumer_sdk"),
        (ThreadPoolConsumerStrategy, "patch_consumer_sdk"),
        (AsyncConsumerStrategy, "patch_async_consumer_sdk"),
    ],
)
def test_consumer_strategies_success_and_complete(
    request,
    strategy_cls,
    patch_fixture,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    factory = patch([[valid_payload_json.encode("utf-8")]])

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed(max_message_count=5)

    assert len(result.successes) == 1
    assert result.successes[0].id == "msg-1"
    assert len(result.failures) == 0
    assert result.failed is False
    assert factory.client.receiver.last_max_message_count == 5
    assert len(factory.client.receiver.completed) == 1


def test_async_consumer_strategy_consume_inside_running_loop(
    patch_async_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    factory = patch_async_consumer_sdk([[valid_payload_json.encode("utf-8")]])
    strategy = AsyncConsumerStrategy(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    async def _runner() -> None:
        result = strategy.consume_parsed(max_message_count=1)
        assert len(result.successes) == 1

    asyncio.run(_runner())
    assert len(factory.client.receiver.completed) == 1


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture",
    [
        (SequentialConsumerStrategy, "patch_consumer_sdk"),
        (ThreadPoolConsumerStrategy, "patch_consumer_sdk"),
        (AsyncConsumerStrategy, "patch_async_consumer_sdk"),
    ],
)
def test_consumer_strategies_collect_errors(
    request,
    strategy_cls,
    patch_fixture,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    invalid_json = '{"id":'
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")

    factory = patch(
        [
            [json.dumps(base_payload).encode("utf-8")],
            [invalid_json.encode("utf-8")],
            [json.dumps(invalid_schema).encode("utf-8")],
        ]
    )

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed(max_message_count=10)

    assert len(result.successes) == 1
    assert len(result.failures) == 2
    assert result.failed is True
    assert len(factory.client.receiver.completed) == 1
    assert len(factory.client.receiver.dead_lettered) == 2


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture",
    [
        (SequentialConsumerStrategy, "patch_consumer_sdk"),
        (ThreadPoolConsumerStrategy, "patch_consumer_sdk"),
        (AsyncConsumerStrategy, "patch_async_consumer_sdk"),
    ],
)
def test_consumer_parse_failure_is_not_completed_with_dead_letter_policy(
    request,
    strategy_cls,
    patch_fixture,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    factory = patch([[b'{"id":']])

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed(max_message_count=1)

    assert len(result.failures) == 1
    assert len(factory.client.receiver.completed) == 0
    assert len(factory.client.receiver.dead_lettered) == 1


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture,policy,settled_field",
    [
        (
            SequentialConsumerStrategy,
            "patch_consumer_sdk",
            "dead_letter",
            "dead_lettered",
        ),
        (SequentialConsumerStrategy, "patch_consumer_sdk", "complete", "completed"),
        (SequentialConsumerStrategy, "patch_consumer_sdk", "abandon", "abandoned"),
        (
            AsyncConsumerStrategy,
            "patch_async_consumer_sdk",
            "dead_letter",
            "dead_lettered",
        ),
    ],
)
def test_consumer_strategies_apply_failure_policy(
    request,
    strategy_cls,
    patch_fixture,
    policy,
    settled_field,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    factory = patch([[b'{"id":']])

    policy_config = ASBConsumerConfig(
        topic_name=consumer_config.topic_name,
        subscription_name=consumer_config.subscription_name,
        parse_failure_policy=policy,
    )
    strategy = strategy_cls(
        connection=connection_config,
        consumer=policy_config,
        parser=alert_message_parser,
    )

    result = strategy.consume_parsed(max_message_count=1)

    assert len(result.failures) == 1
    assert len(getattr(factory.client.receiver, settled_field)) == 1


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture",
    [
        (SequentialConsumerStrategy, "patch_consumer_sdk"),
        (ThreadPoolConsumerStrategy, "patch_consumer_sdk"),
        (AsyncConsumerStrategy, "patch_async_consumer_sdk"),
    ],
)
def test_consumer_strategies_ignore_raise_on_error_flag(
    request,
    strategy_cls,
    patch_fixture,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    patch([[b'{"id":']])

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed()

    assert result.failed is True
    assert len(result.failures) == 1


@pytest.mark.parametrize(
    "strategy_cls,patch_fixture",
    [
        (SequentialConsumerStrategy, "patch_consumer_sdk"),
        (ThreadPoolConsumerStrategy, "patch_consumer_sdk"),
        (AsyncConsumerStrategy, "patch_async_consumer_sdk"),
    ],
)
def test_consumer_strategies_empty_messages(
    request,
    strategy_cls,
    patch_fixture,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    factory = patch([])

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed()

    assert result.successes == []
    assert result.failures == []
    assert factory.client.receiver.completed == []


class RetryableTestError(RuntimeError):
    retryable = True


@pytest.mark.parametrize(
    "strategy_cls",
    [SequentialConsumerStrategy, ThreadPoolConsumerStrategy],
)
def test_sync_consumer_transient_processing_error_abandons_message(
    strategy_cls,
    patch_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    factory = patch_consumer_sdk([[valid_payload_json.encode("utf-8")]])

    def _failing_complete(_msg) -> None:
        raise RetryableTestError("temporary failure")

    factory.client.receiver.complete_message = _failing_complete

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed(max_message_count=1)

    assert len(result.successes) == 0
    assert len(result.failures) == 1
    assert len(factory.client.receiver.abandoned) == 1


@pytest.mark.parametrize(
    "strategy_cls",
    [SequentialConsumerStrategy, ThreadPoolConsumerStrategy],
)
def test_sync_consumer_non_transient_processing_error_is_raised(
    strategy_cls,
    patch_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    factory = patch_consumer_sdk([[valid_payload_json.encode("utf-8")]])

    def _failing_complete(_msg) -> None:
        raise ValueError("non transient")

    factory.client.receiver.complete_message = _failing_complete

    strategy = strategy_cls(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    with pytest.raises(ValueError, match="non transient"):
        strategy.consume_parsed(max_message_count=1)


def test_async_consumer_transient_processing_error_abandons_message(
    patch_async_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    factory = patch_async_consumer_sdk([[valid_payload_json.encode("utf-8")]])

    async def _failing_complete(_msg) -> None:
        raise RetryableTestError("temporary failure")

    factory.client.receiver.complete_message = _failing_complete

    strategy = AsyncConsumerStrategy(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = strategy.consume_parsed(max_message_count=1)

    assert len(result.successes) == 0
    assert len(result.failures) == 1
    assert len(factory.client.receiver.abandoned) == 1


def test_async_consumer_non_transient_processing_error_is_raised(
    patch_async_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    factory = patch_async_consumer_sdk([[valid_payload_json.encode("utf-8")]])

    async def _failing_complete(_msg) -> None:
        raise ValueError("non transient")

    factory.client.receiver.complete_message = _failing_complete

    strategy = AsyncConsumerStrategy(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    with pytest.raises(ValueError, match="non transient"):
        strategy.consume_parsed(max_message_count=1)
