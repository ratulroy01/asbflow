from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from pydantic import BaseModel

from asbflow.config import (
    ASBConnectionConfig,
    ASBConsumerConfig,
    ASBMessageConfig,
    ASBPublisherConfig,
)
from asbflow.shared.parsing import PydanticModelParser


class TestAlertMessage(BaseModel):
    id: str
    alert: dict[str, Any]


# ---------------------------------------------
# pytest markers
# ---------------------------------------------

FOLDER: str = "test/unit/"
MARK: str = "unit"


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Automatically mark all tests in this folder as 'unit'."""
    for item in items:
        if FOLDER in str(item.fspath).replace("\\", "/"):
            item.add_marker(MARK)


# ---------------------------------------------
# Stubs and fixtures
# ---------------------------------------------


class FakeMessageBatch:
    def __init__(self, max_size: int) -> None:
        self._max_size = max_size
        self._messages: list[Any] = []

    def add_message(self, message: Any) -> None:
        if len(self._messages) >= self._max_size:
            raise ValueError("Batch is full")
        self._messages.append(message)

    def __len__(self) -> int:
        return len(self._messages)

    @property
    def messages(self) -> list[Any]:
        return list(self._messages)


class FakeMessage:
    def __init__(self, body: str, **kwargs: Any) -> None:
        self.body_arg: str = body
        self.kwargs: dict[str, Any] = kwargs


class FakeSender:
    def __init__(self, max_batch_size: int = 1000) -> None:
        self.sent: list[Any] = []
        self.max_batch_size: int = max_batch_size

    def __enter__(self) -> "FakeSender":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def send_messages(self, message: Any) -> None:
        self.sent.append(message)

    def create_message_batch(self) -> FakeMessageBatch:
        return FakeMessageBatch(max_size=self.max_batch_size)


class AsyncFakeSender:
    def __init__(self, max_batch_size: int = 1000) -> None:
        self.sent: list[Any] = []
        self.max_batch_size: int = max_batch_size

    async def __aenter__(self) -> "AsyncFakeSender":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def send_messages(self, message: Any) -> None:
        self.sent.append(message)

    async def create_message_batch(self) -> FakeMessageBatch:
        return FakeMessageBatch(max_size=self.max_batch_size)


class FakeReceivedMessage:
    def __init__(self, body: Any) -> None:
        self.body: Any = body


class FakeReceiver:
    def __init__(self, message_bodies: list[Any]) -> None:
        self._message_bodies: list[Any] = message_bodies
        self._cursor: int = 0
        self.completed: list[Any] = []
        self.abandoned: list[Any] = []
        self.dead_lettered: list[Any] = []
        self.last_max_message_count: int | None = None

    def __enter__(self) -> "FakeReceiver":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def receive_messages(self, max_message_count: int = 10) -> list[FakeReceivedMessage]:
        self.last_max_message_count = max_message_count
        start = self._cursor
        end = min(start + max_message_count, len(self._message_bodies))
        self._cursor = end
        return [FakeReceivedMessage(body) for body in self._message_bodies[start:end]]

    def complete_message(self, msg: Any) -> None:
        self.completed.append(msg)

    def abandon_message(self, msg: Any) -> None:
        self.abandoned.append(msg)

    def dead_letter_message(self, msg: Any) -> None:
        self.dead_lettered.append(msg)


class AsyncFakeReceiver:
    def __init__(self, message_bodies: list[Any]) -> None:
        self._message_bodies: list[Any] = message_bodies
        self._cursor: int = 0
        self.completed: list[Any] = []
        self.abandoned: list[Any] = []
        self.dead_lettered: list[Any] = []
        self.last_max_message_count: int | None = None

    async def __aenter__(self) -> "AsyncFakeReceiver":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def receive_messages(self, max_message_count: int = 10) -> list[FakeReceivedMessage]:
        self.last_max_message_count = max_message_count
        start = self._cursor
        end = min(start + max_message_count, len(self._message_bodies))
        self._cursor = end
        return [FakeReceivedMessage(body) for body in self._message_bodies[start:end]]

    async def complete_message(self, msg: Any) -> None:
        self.completed.append(msg)

    async def abandon_message(self, msg: Any) -> None:
        self.abandoned.append(msg)

    async def dead_letter_message(self, msg: Any) -> None:
        self.dead_lettered.append(msg)


class FakeClient:
    def __init__(self, message_bodies: list[Any], max_batch_size: int = 1000) -> None:
        self.sender: FakeSender = FakeSender(max_batch_size=max_batch_size)
        self.receiver: FakeReceiver = FakeReceiver(message_bodies)
        self.sender_kwargs: dict[str, Any] | None = None
        self.receiver_kwargs: dict[str, Any] | None = None
        self.sender_method: str | None = None
        self.receiver_method: str | None = None

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def get_topic_sender(self, **kwargs: Any) -> FakeSender:
        self.sender_kwargs = kwargs
        self.sender_method = "topic"
        return self.sender

    def get_queue_sender(self, **kwargs: Any) -> FakeSender:
        self.sender_kwargs = kwargs
        self.sender_method = "queue"
        return self.sender

    def get_subscription_receiver(self, **kwargs: Any) -> FakeReceiver:
        self.receiver_kwargs = kwargs
        self.receiver_method = "subscription"
        return self.receiver

    def get_queue_receiver(self, **kwargs: Any) -> FakeReceiver:
        self.receiver_kwargs = kwargs
        self.receiver_method = "queue"
        return self.receiver


class AsyncFakeClient:
    def __init__(self, message_bodies: list[Any], max_batch_size: int = 1000) -> None:
        self.sender: AsyncFakeSender = AsyncFakeSender(max_batch_size=max_batch_size)
        self.receiver: AsyncFakeReceiver = AsyncFakeReceiver(message_bodies)
        self.sender_kwargs: dict[str, Any] | None = None
        self.receiver_kwargs: dict[str, Any] | None = None
        self.sender_method: str | None = None
        self.receiver_method: str | None = None

    async def __aenter__(self) -> "AsyncFakeClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def get_topic_sender(self, **kwargs: Any) -> AsyncFakeSender:
        self.sender_kwargs = kwargs
        self.sender_method = "topic"
        return self.sender

    def get_queue_sender(self, **kwargs: Any) -> AsyncFakeSender:
        self.sender_kwargs = kwargs
        self.sender_method = "queue"
        return self.sender

    def get_subscription_receiver(self, **kwargs: Any) -> AsyncFakeReceiver:
        self.receiver_kwargs = kwargs
        self.receiver_method = "subscription"
        return self.receiver

    def get_queue_receiver(self, **kwargs: Any) -> AsyncFakeReceiver:
        self.receiver_kwargs = kwargs
        self.receiver_method = "queue"
        return self.receiver


class FakeServiceBusFactory:
    def __init__(self, message_bodies: list[Any], max_batch_size: int = 1000) -> None:
        self.client_kwargs: dict[str, Any] | None = None
        self.client: FakeClient = FakeClient(message_bodies, max_batch_size=max_batch_size)

    def from_connection_string(self, **kwargs: Any) -> FakeClient:
        self.client_kwargs = kwargs
        return self.client


class AsyncFakeServiceBusFactory:
    def __init__(self, message_bodies: list[Any], max_batch_size: int = 1000) -> None:
        self.client_kwargs: dict[str, Any] | None = None
        self.client: AsyncFakeClient = AsyncFakeClient(message_bodies, max_batch_size=max_batch_size)

    def from_connection_string(self, **kwargs: Any) -> AsyncFakeClient:
        self.client_kwargs = kwargs
        return self.client


@pytest.fixture
def base_payload() -> dict[str, Any]:
    return {
        "template_version": "1.0.0",
        "timestamp": "2026-03-23T10:00:00Z",
        "id": "msg-1",
        "is_valid": True,
        "alert_type": "dynamic",
        "reference_date": {
            "previous": "2026-03-22T00:00:00Z",
            "current": "2026-03-23T00:00:00Z",
        },
        "system": "Pegaso",
        "scope": "Acquired",
        "entity": {"type": "soggetti", "id": 123, "code": "S-123"},
        "alert": {
            "id": 1,
            "group": 1,
            "name": "Test alert",
            "description": "Description",
            "policy": "ALLOW_DUPLICATES",
            "trigger": {
                "type": "RELATIVE_VARIATION",
                "condition": "delta > 10%",
            },
            "state": {
                "previous": "prev",
                "current": "curr",
            },
        },
        "query_result": {
            "hash": "abc123",
            "last_update": "2026-03-23T09:55:00Z",
        },
        "data": {
            "previous": {
                "ref_date": "2026-03-22T00:00:00Z",
                "variables": [{"key": "x", "type": "number", "value": 10}],
            },
            "current": {
                "ref_date": "2026-03-23T00:00:00Z",
                "variables": [{"key": "x", "type": "number", "value": 12}],
            },
            "metrics": [{"key": "delta", "type": "number", "value": 2}],
        },
    }


@pytest.fixture
def static_payload(base_payload: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(base_payload)
    payload["alert_type"] = "static"
    payload["reference_date"]["previous"] = None
    payload["alert"]["state"]["previous"] = None
    payload["data"]["previous"] = None
    return payload


@pytest.fixture
def valid_payload_json(base_payload: dict[str, Any]) -> str:
    return json.dumps(base_payload)


@pytest.fixture
def alert_message(base_payload: dict[str, Any]) -> TestAlertMessage:
    return TestAlertMessage.model_validate(base_payload)


@pytest.fixture
def alert_message_parser() -> PydanticModelParser:
    return PydanticModelParser(TestAlertMessage)


@pytest.fixture
def connection_config() -> ASBConnectionConfig:
    return ASBConnectionConfig(
        connection_string="Endpoint=sb://test/",
        logging_enable=True,
        user_agent="asbflow-tests",
        client_kwargs={"retry_total": 2},
    )


@pytest.fixture
def publisher_config() -> ASBPublisherConfig:
    return ASBPublisherConfig(topic_name="strategie_subottimali", socket_timeout=12.0)


@pytest.fixture
def consumer_config() -> ASBConsumerConfig:
    return ASBConsumerConfig(
        topic_name="strategie_subottimali",
        subscription_name="dataplatform",
        max_wait_time=10,
    )


@pytest.fixture
def message_config() -> ASBMessageConfig:
    return ASBMessageConfig(
        content_type="application/json",
        subject="alert",
        message_id="m-001",
        time_to_live=timedelta(seconds=30),
        scheduled_enqueue_time_utc=datetime(2026, 3, 23, 10, 0, tzinfo=timezone.utc),
        application_properties={"k": "v"},
    )


@pytest.fixture
def servicebus_factory_builder():
    def _build(message_bodies: list[Any], max_batch_size: int = 1000) -> FakeServiceBusFactory:
        return FakeServiceBusFactory(message_bodies, max_batch_size=max_batch_size)

    return _build


@pytest.fixture
def async_servicebus_factory_builder():
    def _build(
        message_bodies: list[Any] | None = None,
        max_batch_size: int = 1000,
    ) -> AsyncFakeServiceBusFactory:
        return AsyncFakeServiceBusFactory(message_bodies or [], max_batch_size=max_batch_size)

    return _build


@pytest.fixture
def patch_publisher_sdk(monkeypatch: pytest.MonkeyPatch, servicebus_factory_builder):
    def _patch(message_bodies: list[Any] | None = None, max_batch_size: int = 1000) -> FakeServiceBusFactory:
        factory = servicebus_factory_builder(message_bodies or [], max_batch_size=max_batch_size)
        monkeypatch.setattr(
            "asbflow.publisher.base.load_asb_message_type",
            lambda: FakeMessage,
        )
        monkeypatch.setattr(
            "asbflow.publisher.strategies.sequential.load_asb_message_type",
            lambda: FakeMessage,
        )
        monkeypatch.setattr(
            "asbflow.publisher.strategies.thread_pool.load_asb_message_type",
            lambda: FakeMessage,
        )
        monkeypatch.setattr(
            "asbflow.auth.providers.load_asb_client_factory",
            lambda: factory,
        )
        return factory

    return _patch


@pytest.fixture
def patch_async_publisher_sdk(
    monkeypatch: pytest.MonkeyPatch,
    async_servicebus_factory_builder,
):
    def _patch(max_batch_size: int = 1000) -> AsyncFakeServiceBusFactory:
        factory = async_servicebus_factory_builder([], max_batch_size=max_batch_size)
        monkeypatch.setattr(
            "asbflow.publisher.strategies.async_strategy.load_asb_message_type",
            lambda: FakeMessage,
        )
        monkeypatch.setattr(
            "asbflow.auth.providers.load_asb_async_client",
            lambda: factory,
        )
        return factory

    return _patch


@pytest.fixture
def patch_consumer_sdk(monkeypatch: pytest.MonkeyPatch, servicebus_factory_builder):
    def _patch(message_bodies: list[Any]) -> FakeServiceBusFactory:
        factory = servicebus_factory_builder(message_bodies)
        monkeypatch.setattr(
            "asbflow.auth.providers.load_asb_client_factory",
            lambda: factory,
        )
        return factory

    return _patch


@pytest.fixture
def patch_async_consumer_sdk(
    monkeypatch: pytest.MonkeyPatch,
    async_servicebus_factory_builder,
):
    def _patch(message_bodies: list[Any]) -> AsyncFakeServiceBusFactory:
        factory = async_servicebus_factory_builder(message_bodies)
        monkeypatch.setattr(
            "asbflow.auth.providers.load_asb_async_client",
            lambda: factory,
        )
        return factory

    return _patch


@pytest.fixture
def patch_dlq_sdk(monkeypatch: pytest.MonkeyPatch, servicebus_factory_builder):
    def _patch(message_bodies: list[Any]) -> FakeServiceBusFactory:
        factory = servicebus_factory_builder(message_bodies)
        monkeypatch.setattr(
            "asbflow.auth.providers.load_asb_client_factory",
            lambda: factory,
        )
        return factory

    return _patch
