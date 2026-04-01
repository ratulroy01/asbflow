import pytest

from asbflow import ASBPublisher, PublishError


def test_publish_batch_empty_payloads_sends_nothing(
    patch_publisher_sdk,
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

    publisher.publish_batch([])

    assert factory.client.sender.sent == []


def test_publish_empty_list_routes_to_batch_and_sends_nothing(
    patch_publisher_sdk,
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

    publisher.publish([])

    assert factory.client.sender.sent == []


def test_publish_batch_chunk_size_larger_than_payloads(
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
    )

    publisher.publish_batch([base_payload, payload_2], chunk_size=10)

    assert len(factory.client.sender.sent) == 1


def test_publish_batch_single_message_too_large_raises(
    patch_publisher_sdk,
    base_payload,
    connection_config,
    publisher_config,
    message_config,
):
    patch_publisher_sdk(max_batch_size=0)
    publisher = ASBPublisher(
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    with pytest.raises(PublishError) as exc_info:
        publisher.publish_batch([base_payload])

    assert exc_info.value.operation == "publish_batch"
    assert isinstance(exc_info.value.error, ValueError)
    assert "exceeds the batch size limit" in str(exc_info.value.error)
