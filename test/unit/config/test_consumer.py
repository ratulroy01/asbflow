import pytest

from asbflow.config import ASBConsumerConfig, ASBMessagingEntity, ParseFailurePolicy


def test_consumer_config_to_receiver_kwargs_includes_optional_and_extra():
    config = ASBConsumerConfig(
        topic_name="topic-a",
        subscription_name="sub-a",
        max_wait_time=10,
        prefetch_count=50,
        client_identifier="cid",
        receiver_kwargs={"auto_lock_renewer": "x"},
    )

    kwargs = config.to_receiver_kwargs()

    assert kwargs["topic_name"] == "topic-a"
    assert kwargs["subscription_name"] == "sub-a"
    assert kwargs["max_wait_time"] == 10
    assert kwargs["prefetch_count"] == 50
    assert kwargs["client_identifier"] == "cid"
    assert kwargs["auto_lock_renewer"] == "x"


def test_consumer_config_to_receiver_kwargs_minimal():
    kwargs = ASBConsumerConfig(topic_name="topic-a", subscription_name="sub-a").to_receiver_kwargs()

    assert kwargs == {
        "topic_name": "topic-a",
        "subscription_name": "sub-a",
    }


def test_consumer_config_queue_entity_receiver_kwargs():
    kwargs = ASBConsumerConfig(
        entity_type=ASBMessagingEntity.QUEUE,
        queue_name="queue-a",
        max_wait_time=10,
    ).to_receiver_kwargs()

    assert kwargs["queue_name"] == "queue-a"
    assert "topic_name" not in kwargs
    assert "subscription_name" not in kwargs


def test_consumer_config_queue_entity_requires_queue_name():
    with pytest.raises(ValueError, match="queue_name is required"):
        ASBConsumerConfig(entity_type=ASBMessagingEntity.QUEUE)


def test_consumer_config_parse_failure_policy_resolution():
    cfg = ASBConsumerConfig(
        topic_name="topic-a",
        subscription_name="sub-a",
        parse_failure_policy="deadletter",
    )
    assert cfg.resolved_parse_failure_policy is ParseFailurePolicy.DEAD_LETTER


def test_consumer_config_parse_failure_policy_invalid_raises():
    cfg = ASBConsumerConfig(
        topic_name="topic-a",
        subscription_name="sub-a",
        parse_failure_policy="bad",
    )

    with pytest.raises(ValueError, match="Unknown parse failure policy"):
        _ = cfg.resolved_parse_failure_policy
