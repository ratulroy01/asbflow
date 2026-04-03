import pytest

from asbflow.publisher.base import BasePublisherStrategy


class DummyPublisherStrategy(BasePublisherStrategy):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.batch_calls: list[tuple[int, int | None]] = []

    def publish_batch(self, payloads, *, chunk_size=None, parse=False, parser=None, message=None) -> None:
        self.batch_calls.append((len(payloads), chunk_size))


def test_base_publish_message_sends_single_message(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    factory = patch_publisher_sdk()
    strategy = DummyPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish_message(base_payload)

    assert len(factory.client.sender.sent) == 1


def test_base_publish_routes_to_batch_when_sequence(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    patch_publisher_sdk()
    strategy = DummyPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish([base_payload, base_payload], chunk_size=2)

    assert strategy.batch_calls == [(2, 2)]


def test_base_publish_routes_to_single_when_mapping(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    factory = patch_publisher_sdk()
    strategy = DummyPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    strategy.publish(base_payload)

    assert strategy.batch_calls == []
    assert len(factory.client.sender.sent) == 1


def test_base_chunk_size_validation(
    patch_publisher_sdk,
    connection_config,
    publisher_config,
    message_config,
):
    patch_publisher_sdk()
    strategy = DummyPublisherStrategy(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    with pytest.raises(ValueError, match="chunk_size must be a positive integer"):
        strategy._validate_chunk_size(0)
