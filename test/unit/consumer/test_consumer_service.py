import asyncio
import json

import pytest

from asbflow import ASBConsumer, ConsumeError
from asbflow.config import ASBConsumerConfig
from asbflow.consumer.factory import ConsumeExecutionMode


@pytest.mark.parametrize(
    "execution_mode,patch_fixture",
    [
        (ConsumeExecutionMode.SEQUENTIAL, "patch_consumer_sdk"),
        ("thread_pool", "patch_consumer_sdk"),
        ("async", "patch_async_consumer_sdk"),
    ],
)
def test_service_consume_success(
    request,
    execution_mode,
    patch_fixture,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)
    patch([[valid_payload_json.encode("utf-8")]])

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode=execution_mode,
        parser=alert_message_parser,
    )

    result = consumer.consume_parsed(max_message_count=3)

    assert len(result.successes) == 1
    assert result.successes[0].id == "msg-1"


def test_service_default_raise_on_error_true(
    patch_consumer_sdk,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_consumer_sdk([[b'{"id":']])
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    with pytest.raises(ConsumeError):
        consumer.consume_parsed()


def test_service_raise_on_error_default_can_be_disabled(
    patch_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")
    patch_consumer_sdk([[json.dumps(invalid_schema).encode("utf-8")]])

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
        raise_on_error=False,
    )
    result = consumer.consume_parsed()

    assert result.failed is True
    assert len(result.failures) == 1


def test_service_consume_all_with_leave_unsettled_guard(
    patch_consumer_sdk,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_consumer_sdk([[b'{"id":']])

    guarded_consumer_cfg = ASBConsumerConfig(
        topic_name=consumer_config.topic_name,
        subscription_name=consumer_config.subscription_name,
        parse_failure_policy="leave_unsettled",
    )
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=guarded_consumer_cfg,
        parser=alert_message_parser,
    )

    with pytest.raises(RuntimeError, match="cannot progress"):
        consumer.consume_all(max_message_count=1, parse=True)


def test_service_aconsume_all_with_leave_unsettled_guard(
    patch_async_consumer_sdk,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_async_consumer_sdk([[b'{"id":']])

    guarded_consumer_cfg = ASBConsumerConfig(
        topic_name=consumer_config.topic_name,
        subscription_name=consumer_config.subscription_name,
        parse_failure_policy="leave_unsettled",
    )
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=guarded_consumer_cfg,
        execution_mode="async",
        parser=alert_message_parser,
    )

    with pytest.raises(RuntimeError, match="cannot progress"):
        asyncio.run(consumer.aconsume_all(max_message_count=1, parse=True))


@pytest.mark.parametrize(
    "execution_mode,patch_fixture",
    [
        (ConsumeExecutionMode.SEQUENTIAL, "patch_consumer_sdk"),
        ("thread_pool", "patch_consumer_sdk"),
        ("async", "patch_async_consumer_sdk"),
    ],
)
def test_service_consume_all_drains_multiple_batches(
    request,
    execution_mode,
    patch_fixture,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch = request.getfixturevalue(patch_fixture)

    payload_1 = dict(base_payload)
    payload_1["id"] = "msg-1"
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"
    payload_3 = dict(base_payload)
    payload_3["id"] = "msg-3"

    factory = patch(
        [
            [json.dumps(payload_1).encode("utf-8")],
            [json.dumps(payload_2).encode("utf-8")],
            [json.dumps(payload_3).encode("utf-8")],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode=execution_mode,
        parser=alert_message_parser,
    )

    result = consumer.consume_all(max_message_count=2, parse=True)

    assert [message.id for message in result.successes] == ["msg-1", "msg-2", "msg-3"]
    assert result.failures == []
    assert factory.client.receiver.last_max_message_count == 2


def test_service_aconsume_all_drains_multiple_batches(
    patch_async_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    payload_1 = dict(base_payload)
    payload_1["id"] = "msg-1"
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"
    payload_3 = dict(base_payload)
    payload_3["id"] = "msg-3"

    factory = patch_async_consumer_sdk(
        [
            [json.dumps(payload_1).encode("utf-8")],
            [json.dumps(payload_2).encode("utf-8")],
            [json.dumps(payload_3).encode("utf-8")],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
        parser=alert_message_parser,
    )

    result = asyncio.run(consumer.aconsume_all(max_message_count=2, parse=True))

    assert [message.id for message in result.successes] == ["msg-1", "msg-2", "msg-3"]
    assert result.failures == []
    assert factory.client.receiver.last_max_message_count == 2


def test_service_consume_all_raise_on_error(
    patch_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")

    patch_consumer_sdk(
        [
            [json.dumps(base_payload).encode("utf-8")],
            [json.dumps(invalid_schema).encode("utf-8")],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
        raise_on_error=False,
    )

    with pytest.raises(ConsumeError) as exc_info:
        consumer.consume_all(max_message_count=1, parse=True, raise_on_error=True)

    assert len(exc_info.value.result.successes) == 1
    assert len(exc_info.value.result.failures) == 1


def test_service_aconsume_all_raise_on_error(
    patch_async_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")

    patch_async_consumer_sdk(
        [
            [json.dumps(base_payload).encode("utf-8")],
            [json.dumps(invalid_schema).encode("utf-8")],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
        parser=alert_message_parser,
        raise_on_error=False,
    )

    with pytest.raises(ConsumeError) as exc_info:
        asyncio.run(consumer.aconsume_all(max_message_count=1, parse=True, raise_on_error=True))

    assert len(exc_info.value.result.successes) == 1
    assert len(exc_info.value.result.failures) == 1


def test_service_raise_on_error(
    patch_consumer_sdk,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_consumer_sdk([[b'{"id":']])

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    with pytest.raises(ConsumeError):
        consumer.consume_parsed(raise_on_error=True)


def test_service_invalid_execution_mode_raises(
    connection_config,
    consumer_config,
):
    with pytest.raises(ValueError, match="Unknown consume execution mode"):
        ASBConsumer(
            connection=connection_config,
            consumer=consumer_config,
            execution_mode="invalid",
        )


def test_service_consume_collects_validation_error(
    patch_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")
    patch_consumer_sdk([[json.dumps(invalid_schema).encode("utf-8")]])

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = consumer.consume_parsed(raise_on_error=False)

    assert result.failed is True
    assert len(result.failures) == 1


def test_service_aconsume_with_async_mode(
    patch_async_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_async_consumer_sdk([[valid_payload_json.encode("utf-8")]])
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
        parser=alert_message_parser,
    )

    result = asyncio.run(consumer.aconsume_parsed(max_message_count=1))

    assert len(result.successes) == 1
    assert result.successes[0].id == "msg-1"


def test_service_aconsume_raises_if_strategy_not_async(
    connection_config,
    consumer_config,
):
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="sequential",
    )

    with pytest.raises(ValueError, match="only when execution_mode is 'async'"):
        asyncio.run(consumer.aconsume())


def test_service_aconsume_all_raises_if_strategy_not_async(
    connection_config,
    consumer_config,
):
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="sequential",
    )

    with pytest.raises(ValueError, match="only when execution_mode is 'async'"):
        asyncio.run(consumer.aconsume_all())


def test_service_consume_with_async_strategy_inside_running_loop(
    patch_async_consumer_sdk,
    valid_payload_json,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_async_consumer_sdk([[valid_payload_json.encode("utf-8")]])
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
        parser=alert_message_parser,
    )

    async def _runner() -> None:
        result = consumer.consume_parsed(max_message_count=1)
        assert len(result.successes) == 1

    asyncio.run(_runner())


def test_service_injects_failure_handler_into_strategy(
    monkeypatch,
    connection_config,
    consumer_config,
):
    from asbflow.consumer.failure_handler import ConsumeFailureHandler
    from asbflow.consumer.result import RawConsumeResult

    captured = {}

    class _FakeStrategy:
        parse_failure_policy = consumer_config.resolved_parse_failure_policy

        def consume(
            self,
            max_message_count: int = 10,
            *,
            parse: bool = False,
            failure_handler=None,
            parser=None,
            settle_messages: bool = True,
        ) -> RawConsumeResult:
            captured["failure_handler"] = failure_handler
            return RawConsumeResult()

    monkeypatch.setattr(
        "asbflow.consumer.service.ConsumerFactory.create_strategy",
        lambda *args, **kwargs: _FakeStrategy(),
    )

    consumer = ASBConsumer(connection=connection_config, consumer=consumer_config)
    consumer.consume()

    assert isinstance(captured["failure_handler"], ConsumeFailureHandler)


def test_service_exposes_configuration(
    connection_config,
    consumer_config,
):
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="thread_pool",
    )

    assert consumer.connection_config is connection_config
    assert consumer.consumer_config is consumer_config
    assert consumer.execution_mode is ConsumeExecutionMode.THREAD_POOL
    assert consumer.raise_on_error is True


def test_service_consume_all_raw_drains_multiple_batches(
    patch_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    payload_1 = dict(base_payload)
    payload_1["id"] = "msg-1"
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    patch_consumer_sdk(
        [
            [json.dumps(payload_1).encode("utf-8")],
            [json.dumps(payload_2).encode("utf-8")],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
    )

    result = consumer.consume_all(max_message_count=2, parse=False)

    assert [message["id"] for message in result.successes] == ["msg-1", "msg-2"]
    assert result.failures == []


def test_service_aconsume_all_raw_drains_multiple_batches(
    patch_async_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    payload_1 = dict(base_payload)
    payload_1["id"] = "msg-1"
    payload_2 = dict(base_payload)
    payload_2["id"] = "msg-2"

    patch_async_consumer_sdk(
        [
            [json.dumps(payload_1).encode("utf-8")],
            [json.dumps(payload_2).encode("utf-8")],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
    )

    result = asyncio.run(consumer.aconsume_all(max_message_count=2, parse=False))

    assert [message["id"] for message in result.successes] == ["msg-1", "msg-2"]
    assert result.failures == []


def test_service_consume_raw_raises_on_error(
    patch_consumer_sdk,
    connection_config,
    consumer_config,
):
    patch_consumer_sdk([[b'{"id":']])
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
    )

    with pytest.raises(ConsumeError):
        consumer.consume(parse=False, raise_on_error=True)


def test_service_consume_all_raw_raise_on_error(
    patch_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    patch_consumer_sdk(
        [
            [json.dumps(base_payload).encode("utf-8")],
            [b'{"id":'],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        raise_on_error=False,
    )

    with pytest.raises(ConsumeError) as exc_info:
        consumer.consume_all(max_message_count=1, parse=False, raise_on_error=True)

    assert len(exc_info.value.result.successes) == 1
    assert len(exc_info.value.result.failures) == 1


def test_service_aconsume_all_raw_raise_on_error(
    patch_async_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    patch_async_consumer_sdk(
        [
            [json.dumps(base_payload).encode("utf-8")],
            [b'{"id":'],
        ]
    )

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
        raise_on_error=False,
    )

    with pytest.raises(ConsumeError) as exc_info:
        asyncio.run(consumer.aconsume_all(max_message_count=1, parse=False, raise_on_error=True))

    assert len(exc_info.value.result.successes) == 1
    assert len(exc_info.value.result.failures) == 1


def test_service_aconsume_raw_raises_on_error(
    patch_async_consumer_sdk,
    connection_config,
    consumer_config,
):
    patch_async_consumer_sdk([[b'{"id":']])
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode="async",
    )

    with pytest.raises(ConsumeError):
        asyncio.run(consumer.aconsume(parse=False, raise_on_error=True))


def test_service_read_leaves_messages_unsettled(
    patch_consumer_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    factory = patch_consumer_sdk([json.dumps(base_payload).encode("utf-8")])

    consumer = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
    )

    result = consumer.read(max_message_count=1, parse=False, raise_on_error=False)

    from asbflow.consumer.result import RawConsumeResult

    assert isinstance(result, RawConsumeResult)
    assert len(result.successes) == 1
    assert len(factory.client.receiver.completed) == 0


def test_service_consume_uses_queue_receiver_when_configured(
    patch_consumer_sdk,
    valid_payload_json,
    connection_config,
    alert_message_parser,
):
    from asbflow.config import ASBMessagingEntity

    queue_consumer_config = ASBConsumerConfig(
        entity_type=ASBMessagingEntity.QUEUE,
        queue_name="queue-a",
        max_wait_time=10,
    )

    factory = patch_consumer_sdk([[valid_payload_json.encode("utf-8")]])
    consumer = ASBConsumer(
        connection=connection_config,
        consumer=queue_consumer_config,
        parser=alert_message_parser,
        raise_on_error=False,
    )

    _ = consumer.consume(max_message_count=1, parse=True, raise_on_error=False)

    assert factory.client.receiver_method == "queue"
    assert factory.client.receiver_kwargs is not None
    assert factory.client.receiver_kwargs["queue_name"] == "queue-a"
