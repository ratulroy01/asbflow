from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from asbflow.auth import ASBClientProvider, ASBClientProviderFactory
from asbflow.config import ASBConnectionConfig, ASBMessageConfig, ASBPublisherConfig
from asbflow.entity import ASBEntityClient, ASBEntityClientFactory
from asbflow.shared.asb_ops import ServiceBusPayloadOperations
from asbflow.shared.parsing import PydanticModelParser
from asbflow.shared.payloads import (
    PayloadMapping,
    PayloadNormalizer,
    PublishablePayload,
    PublishInput,
)
from asbflow.shared.sdk import ASBMessageType, load_asb_message_type


class BasePublisherStrategy(ABC):
    def __init__(
        self,
        connection: ASBConnectionConfig,
        publisher: ASBPublisherConfig,
        message: ASBMessageConfig | None = None,
        parser: PydanticModelParser | None = None,
        payload_normalizer: PayloadNormalizer | None = None,
        asb_operations: ServiceBusPayloadOperations | None = None,
        client_provider: ASBClientProvider | None = None,
        entity_client: ASBEntityClient | None = None,
    ) -> None:
        self._connection: ASBConnectionConfig = connection
        self._publisher: ASBPublisherConfig = publisher
        self._message: ASBMessageConfig = message or ASBMessageConfig()
        self._payload_normalizer: PayloadNormalizer = payload_normalizer or PayloadNormalizer(parser)
        self._asb_operations: ServiceBusPayloadOperations = asb_operations or ServiceBusPayloadOperations()
        self._client_provider: ASBClientProvider = client_provider or ASBClientProviderFactory.create(connection)
        self._entity_client: ASBEntityClient = entity_client or ASBEntityClientFactory.create_for_publisher(publisher)

    @property
    def connection_config(self) -> ASBConnectionConfig:
        return self._connection

    @property
    def publisher_config(self) -> ASBPublisherConfig:
        return self._publisher

    @property
    def message_config(self) -> ASBMessageConfig:
        return self._message

    @property
    def parser(self) -> PydanticModelParser | None:
        return self._payload_normalizer.parser

    @property
    def parser_or_raise(self) -> PydanticModelParser:
        return self._payload_normalizer.parser_or_raise

    def publish_message(
        self,
        payload: PublishablePayload,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        normalized_payload = self._payload_normalizer.normalize_payload(
            payload,
            parse=parse,
            parser=parser,
        )
        payload_json: str = self._asb_operations.payload_to_json(normalized_payload)

        servicebus_message: ASBMessageType = load_asb_message_type()
        with self._client_provider.create_sync_client() as client:
            with self._entity_client.get_sync_sender(client, self._publisher) as sender:
                message_object: Any = servicebus_message(
                    payload_json,
                    **self._message.to_message_kwargs(),
                )
                sender.send_messages(message_object)

    @abstractmethod
    def publish_batch(
        self,
        payloads: list[PublishablePayload],
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        raise NotImplementedError

    def publish(
        self,
        payload: PublishInput,
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        if self._is_batch_payload(payload):
            assert isinstance(payload, list)
            self.publish_batch(
                payload,
                chunk_size=chunk_size,
                parse=parse,
                parser=parser,
            )
            return

        assert not isinstance(payload, list)
        self.publish_message(payload, parse=parse, parser=parser)

    @staticmethod
    def _is_batch_payload(payload: PublishInput) -> bool:
        return isinstance(payload, list)

    @staticmethod
    def _validate_chunk_size(chunk_size: int | None) -> None:
        ServiceBusPayloadOperations.validate_chunk_size(chunk_size)

    def _build_servicebus_messages(
        self,
        payloads: list[PublishablePayload],
        *,
        servicebus_message: Any,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> list[object]:
        normalized_payloads: list[PublishablePayload] = self._payload_normalizer.normalize_payloads(
            payloads,
            parse=parse,
            parser=parser,
        )
        return self._asb_operations.build_messages(
            normalized_payloads,
            servicebus_message=servicebus_message,
            message_kwargs=self._message.to_message_kwargs(),
        )

    def _build_sync_batches(
        self,
        sender: Any,
        messages: list[object],
        *,
        chunk_size: int | None = None,
    ) -> list[object]:
        return self._asb_operations.build_sync_batches(
            sender,
            messages,
            chunk_size=chunk_size,
        )


__all__ = [
    "BasePublisherStrategy",
    "PayloadMapping",
    "PublishablePayload",
    "PublishInput",
]
