import json
from copy import deepcopy

import pytest

from asbflow import (
    ASBConsumer,
    ASBDLQManager,
    ASBPublisher,
    DLQError,
    DLQParsedReadResult,
    DLQPublisherNotConfiguredError,
    DLQRawReadResult,
)
from asbflow.dlq import create_dlq_manager
from asbflow.shared.parsing import PydanticModelParser


class _DummyPublisher:
    def __init__(self, fail_for_ids: set[str] | None = None) -> None:
        self.published_ids: list[str] = []
        self.fail_for_ids: set[str] = fail_for_ids or set()

    def publish(
        self,
        payload,
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        payload_id = payload.id if hasattr(payload, "id") else payload.get("id")
        if payload_id in self.fail_for_ids:
            raise RuntimeError("simulated publish failure")
        self.published_ids.append(payload_id)


def test_dlq_read_raw_raises_by_default_on_failures(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    valid_body = json.dumps(base_payload).encode("utf-8")
    invalid_body = b'{"id":'

    patch_dlq_sdk([valid_body, invalid_body])
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
    )

    with pytest.raises(DLQError) as exc_info:
        manager.read(max_message_count=10)

    assert exc_info.value.operation == "read"


def test_dlq_read_raw_with_override(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    valid_body = json.dumps(base_payload).encode("utf-8")
    invalid_body = b'{"id":'

    factory = patch_dlq_sdk([valid_body, invalid_body])
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
    )

    result = manager.consume(max_message_count=10, raise_on_error=False)

    assert isinstance(result, DLQRawReadResult)
    assert len(result.messages) == 1
    assert result.messages[0]["id"] == "msg-1"
    assert len(result.failures) == 1
    assert result.failed is True
    assert result.succeeded is False
    assert len(factory.client.receiver.completed) == 1


def test_dlq_read_raw_without_consuming_leaves_messages_unsettled(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    valid_body = json.dumps(base_payload).encode("utf-8")

    factory = patch_dlq_sdk([valid_body])
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
    )

    result = manager.read(max_message_count=10, parse=False, raise_on_error=False)

    assert isinstance(result, DLQRawReadResult)
    assert len(result.messages) == 1
    assert len(factory.client.receiver.completed) == 0


def test_dlq_read_parsed_without_consuming_leaves_messages_unsettled(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    valid_body = json.dumps(base_payload).encode("utf-8")

    factory = patch_dlq_sdk([valid_body])
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    result = manager.read_parsed(
        max_message_count=10,
        raise_on_error=False,
    )

    assert isinstance(result, DLQParsedReadResult)
    assert len(result.successes) == 1
    assert len(factory.client.receiver.completed) == 0


def test_dlq_read_parse_true_returns_parsed_result_type(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    patch_dlq_sdk([json.dumps(base_payload).encode("utf-8")])
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )

    result = manager.read(max_message_count=10, parse=True, raise_on_error=False)

    assert isinstance(result, DLQParsedReadResult)
    assert len(result.successes) == 1


def test_dlq_read_parsed_collects_parse_failures(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")

    bodies = [
        json.dumps(base_payload).encode("utf-8"),
        json.dumps(invalid_schema).encode("utf-8"),
    ]
    patch_dlq_sdk(bodies)

    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        parser=alert_message_parser,
    )
    result = manager.read_parsed(max_message_count=10, raise_on_error=False)

    assert isinstance(result, DLQParsedReadResult)
    assert len(result.parsed) == 1
    assert result.parsed[0].id == "msg-1"  # type: ignore
    assert len(result.failures) == 1


def test_dlq_redrive_without_publisher_raises(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    patch_dlq_sdk([json.dumps(base_payload).encode("utf-8")])
    manager = create_dlq_manager(connection=connection_config, consumer=consumer_config)

    with pytest.raises(DLQPublisherNotConfiguredError):
        manager.redrive(max_message_count=10)


def test_dlq_redrive_raw_raises_by_default_on_publish_failures(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    payload_ok = deepcopy(base_payload)
    payload_ok["id"] = "ok-1"
    payload_fail_publish = deepcopy(base_payload)
    payload_fail_publish["id"] = "ko-1"

    bodies = [
        json.dumps(payload_ok).encode("utf-8"),
        json.dumps(payload_fail_publish).encode("utf-8"),
    ]

    patch_dlq_sdk(bodies)
    publisher = _DummyPublisher(fail_for_ids={"ko-1"})
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        publisher=publisher,
    )

    with pytest.raises(DLQError) as exc_info:
        manager.redrive(max_message_count=10)

    assert exc_info.value.operation == "redrive"


def test_dlq_redrive_raw_with_override(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    payload_ok = deepcopy(base_payload)
    payload_ok["id"] = "ok-1"
    payload_fail_publish = deepcopy(base_payload)
    payload_fail_publish["id"] = "ko-1"

    bodies = [
        json.dumps(payload_ok).encode("utf-8"),
        json.dumps(payload_fail_publish).encode("utf-8"),
    ]

    patch_dlq_sdk(bodies)
    publisher = _DummyPublisher(fail_for_ids={"ko-1"})
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        publisher=publisher,
    )

    result = manager.redrive(max_message_count=10, raise_on_error=False)

    assert result.republished == 1
    assert result.publish_failed == 1
    assert result.parse_failed == 0
    assert result.failed is True
    assert result.succeeded is False


def test_dlq_redrive_parsed_counts_parse_failures(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
    alert_message_parser,
):
    payload_ok = deepcopy(base_payload)
    payload_ok["id"] = "ok-1"
    invalid_schema = dict(base_payload)
    invalid_schema.pop("alert")

    bodies = [
        json.dumps(payload_ok).encode("utf-8"),
        json.dumps(invalid_schema).encode("utf-8"),
    ]

    patch_dlq_sdk(bodies)
    publisher = _DummyPublisher()
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        publisher=publisher,
        parser=alert_message_parser,
    )

    result = manager.redrive_parsed(max_message_count=10, raise_on_error=False)

    assert result.republished == 1
    assert result.parse_failed == 1
    assert result.publish_failed == 0


def test_dlq_purge_completes_all_received(
    patch_dlq_sdk,
    base_payload,
    connection_config,
    consumer_config,
):
    bodies = [
        json.dumps(base_payload).encode("utf-8"),
        json.dumps(base_payload).encode("utf-8"),
    ]

    factory = patch_dlq_sdk(bodies)
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
    )

    purge_result = manager.purge(max_message_count=10)

    assert purge_result.purged == 2
    assert purge_result.errors == 0
    assert purge_result.succeeded is True
    assert purge_result.failed is False
    assert len(factory.client.receiver.completed) == 2


def test_dlq_service_exposes_configuration_when_configs_passed(
    connection_config,
    consumer_config,
    publisher_config,
):
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
        publisher=publisher_config,
    )

    assert isinstance(manager._consumer, ASBConsumer)
    assert isinstance(manager._publisher, ASBPublisher)
    assert manager.consumer_config is not None
    assert manager.consumer_config.topic_name == consumer_config.topic_name
    assert manager.publisher_config is publisher_config
    assert manager.raise_on_error is True


def test_dlq_service_accepts_consumer_and_publisher_services(
    connection_config,
    consumer_config,
    publisher_config,
):
    consumer_service = ASBConsumer(
        connection=connection_config,
        consumer=consumer_config,
    )
    publisher_service = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
    )

    manager = ASBDLQManager(
        consumer=consumer_service,
        publisher=publisher_service,
    )

    assert manager._consumer is consumer_service
    assert manager._publisher is publisher_service
    assert manager.consumer_config is consumer_config
    assert manager.publisher_config is publisher_config


def test_create_dlq_manager_forces_dlq_subqueue_when_missing(
    connection_config,
    consumer_config,
):
    manager = create_dlq_manager(
        connection=connection_config,
        consumer=consumer_config,
    )

    assert manager.consumer_config is not None
    assert manager.consumer_config.sub_queue is not None
