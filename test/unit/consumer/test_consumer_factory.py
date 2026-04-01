import pytest

from asbflow.consumer.factory import (
    ConsumeExecutionMode,
    ConsumerFactory,
    create_consumer,
)
from asbflow.consumer.strategies import (
    AsyncConsumerStrategy,
    SequentialConsumerStrategy,
    ThreadPoolConsumerStrategy,
)


@pytest.mark.parametrize(
    "mode,expected",
    [
        (ConsumeExecutionMode.SEQUENTIAL, SequentialConsumerStrategy),
        ("sequential", SequentialConsumerStrategy),
        ("serial", SequentialConsumerStrategy),
        (ConsumeExecutionMode.THREAD_POOL, ThreadPoolConsumerStrategy),
        ("thread_pool", ThreadPoolConsumerStrategy),
        ("threadPooled", ThreadPoolConsumerStrategy),
        (ConsumeExecutionMode.ASYNC, AsyncConsumerStrategy),
        ("async", AsyncConsumerStrategy),
        ("asyncio", AsyncConsumerStrategy),
    ],
)
def test_factory_creates_expected_strategy(
    mode,
    expected,
    connection_config,
    consumer_config,
):
    strategy = ConsumerFactory.create_strategy(
        mode,
        connection=connection_config,
        consumer=consumer_config,
    )

    assert isinstance(strategy, expected)


@pytest.mark.parametrize(
    "mode,expected",
    [
        (ConsumeExecutionMode.SEQUENTIAL, SequentialConsumerStrategy),
        (ConsumeExecutionMode.THREAD_POOL, ThreadPoolConsumerStrategy),
        (ConsumeExecutionMode.ASYNC, AsyncConsumerStrategy),
    ],
)
def test_consumer_factory_create_strategy(mode, expected, connection_config, consumer_config):
    strategy = ConsumerFactory.create_strategy(
        mode,
        connection=connection_config,
        consumer=consumer_config,
    )
    assert isinstance(strategy, expected)


def test_factory_invalid_mode_raises(
    connection_config,
    consumer_config,
):
    with pytest.raises(ValueError, match="Unknown consume execution mode"):
        ConsumerFactory.create_strategy(
            "not-valid",
            connection=connection_config,
            consumer=consumer_config,
        )


def test_consumer_factory_create_service_uses_create_strategy(
    monkeypatch,
    connection_config,
    consumer_config,
):
    called = {"value": False}
    strategy = ConsumerFactory.create_strategy(
        ConsumeExecutionMode.SEQUENTIAL,
        connection=connection_config,
        consumer=consumer_config,
    )

    def _fake_create_strategy(*args, **kwargs):
        called["value"] = True
        return strategy

    monkeypatch.setattr(ConsumerFactory, "create_strategy", staticmethod(_fake_create_strategy))

    service = ConsumerFactory.create_service(
        connection=connection_config,
        consumer=consumer_config,
        execution_mode=ConsumeExecutionMode.SEQUENTIAL,
    )

    assert called["value"] is True
    assert service.connection_config is connection_config
    assert service.consumer_config is consumer_config


def test_create_consumer_service(connection_config, consumer_config):
    service = create_consumer(connection=connection_config, consumer=consumer_config)
    assert service.connection_config is connection_config
    assert service.consumer_config is consumer_config
