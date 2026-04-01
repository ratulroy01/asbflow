from asbflow.config import ASBConsumerConfig, ASBMessagingEntity, ASBPublisherConfig
from asbflow.entity import ASBEntityClientFactory, QueueEntityClient, TopicEntityClient


def test_entity_factory_create_for_publisher_topic():
    config = ASBPublisherConfig(topic_name="topic-a")
    provider = ASBEntityClientFactory.create_for_publisher(config)
    assert isinstance(provider, TopicEntityClient)


def test_entity_factory_create_for_publisher_queue():
    config = ASBPublisherConfig(entity_type=ASBMessagingEntity.QUEUE, queue_name="queue-a")
    provider = ASBEntityClientFactory.create_for_publisher(config)
    assert isinstance(provider, QueueEntityClient)


def test_entity_factory_create_for_consumer_topic():
    config = ASBConsumerConfig(topic_name="topic-a", subscription_name="sub-a")
    provider = ASBEntityClientFactory.create_for_consumer(config)
    assert isinstance(provider, TopicEntityClient)


def test_entity_factory_create_for_consumer_queue():
    config = ASBConsumerConfig(entity_type=ASBMessagingEntity.QUEUE, queue_name="queue-a")
    provider = ASBEntityClientFactory.create_for_consumer(config)
    assert isinstance(provider, QueueEntityClient)
