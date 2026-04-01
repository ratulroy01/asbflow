import pytest

from asbflow.publisher.factory import (
    PublisherFactory,
    PublishExecutionMode,
    create_publisher,
)
from asbflow.publisher.strategies import (
    AsyncPublisherStrategy,
    SequentialPublisherStrategy,
    ThreadPoolPublisherStrategy,
)


@pytest.mark.parametrize(
    "mode,expected",
    [
        (PublishExecutionMode.SEQUENTIAL, SequentialPublisherStrategy),
        ("sequential", SequentialPublisherStrategy),
        ("serial", SequentialPublisherStrategy),
        (PublishExecutionMode.THREAD_POOL, ThreadPoolPublisherStrategy),
        ("thread_pool", ThreadPoolPublisherStrategy),
        ("threadPooled", ThreadPoolPublisherStrategy),
        (PublishExecutionMode.ASYNC, AsyncPublisherStrategy),
        ("async", AsyncPublisherStrategy),
        ("asyncio", AsyncPublisherStrategy),
    ],
)
def test_factory_creates_expected_strategy(
    mode,
    expected,
    connection_config,
    publisher_config,
    message_config,
):
    strategy = PublisherFactory.create_strategy(
        mode,
        connection=connection_config,
        publisher=publisher_config,
        message=message_config,
    )

    assert isinstance(strategy, expected)


@pytest.mark.parametrize(
    "mode,expected",
    [
        (PublishExecutionMode.SEQUENTIAL, SequentialPublisherStrategy),
        (PublishExecutionMode.THREAD_POOL, ThreadPoolPublisherStrategy),
        (PublishExecutionMode.ASYNC, AsyncPublisherStrategy),
    ],
)
def test_publisher_factory_create_strategy(mode, expected, connection_config, publisher_config):
    strategy = PublisherFactory.create_strategy(
        mode,
        connection=connection_config,
        publisher=publisher_config,
    )
    assert isinstance(strategy, expected)


def test_factory_invalid_mode_raises(
    connection_config,
    publisher_config,
    message_config,
):
    with pytest.raises(ValueError, match="Unknown publish execution mode"):
        PublisherFactory.create_strategy(
            "not-valid",
            connection=connection_config,
            publisher=publisher_config,
            message=message_config,
        )


def test_publisher_factory_create_service_uses_create_strategy(
    monkeypatch,
    connection_config,
    publisher_config,
):
    called = {"value": False}
    strategy = PublisherFactory.create_strategy(
        PublishExecutionMode.SEQUENTIAL,
        connection=connection_config,
        publisher=publisher_config,
    )

    def _fake_create_strategy(*args, **kwargs):
        called["value"] = True
        return strategy

    monkeypatch.setattr(PublisherFactory, "create_strategy", staticmethod(_fake_create_strategy))

    service = PublisherFactory.create_service(
        connection=connection_config,
        publisher=publisher_config,
        execution_mode=PublishExecutionMode.SEQUENTIAL,
    )

    assert called["value"] is True
    assert service.connection_config is connection_config
    assert service.publisher_config is publisher_config


def test_create_publisher_service(connection_config, publisher_config):
    service = create_publisher(connection=connection_config, publisher=publisher_config)
    assert service.connection_config is connection_config
    assert service.publisher_config is publisher_config
