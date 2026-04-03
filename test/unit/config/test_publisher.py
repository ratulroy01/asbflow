import pytest

from asbflow.config import ASBMessagingEntity, ASBPublisherConfig


def test_publisher_config_to_sender_kwargs_includes_optional_and_extra():
    config = ASBPublisherConfig(
        topic_name="topic-a",
        client_identifier="cid",
        socket_timeout=9.5,
        sender_kwargs={"keep_alive": True},
    )

    kwargs = config.to_sender_kwargs()

    assert kwargs == {
        "topic_name": "topic-a",
        "client_identifier": "cid",
        "socket_timeout": 9.5,
        "keep_alive": True,
    }


def test_publisher_config_queue_entity_sender_kwargs():
    config = ASBPublisherConfig(
        entity_type=ASBMessagingEntity.QUEUE,
        queue_name="queue-a",
        client_identifier="cid",
    )

    kwargs = config.to_sender_kwargs()

    assert kwargs["queue_name"] == "queue-a"
    assert "topic_name" not in kwargs


def test_publisher_config_queue_entity_requires_queue_name():
    with pytest.raises(ValueError, match="queue_name is required"):
        ASBPublisherConfig(entity_type=ASBMessagingEntity.QUEUE)
