from datetime import datetime, timedelta, timezone

import pytest

from asbflow.config import ASBMessageConfig, ASBMessagingEntity, ASBPublisherConfig


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


def test_message_config_to_message_kwargs_includes_optional_and_extra():
    config = ASBMessageConfig(
        content_type="application/json",
        message_id="mid",
        subject="subject",
        time_to_live=timedelta(minutes=1),
        scheduled_enqueue_time_utc=datetime(2026, 3, 23, 12, 0, tzinfo=timezone.utc),
        application_properties={"k": "v"},
        message_kwargs={"session_id": "sid"},
    )

    kwargs = config.to_message_kwargs()

    assert kwargs["content_type"] == "application/json"
    assert kwargs["message_id"] == "mid"
    assert kwargs["subject"] == "subject"
    assert kwargs["time_to_live"] == timedelta(minutes=1)
    assert kwargs["scheduled_enqueue_time_utc"] == datetime(2026, 3, 23, 12, 0, tzinfo=timezone.utc)
    assert kwargs["application_properties"] == {"k": "v"}
    assert kwargs["session_id"] == "sid"
