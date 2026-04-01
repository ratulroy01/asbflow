from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from asbflow.auth import ASBClientProvider, ASBClientProviderFactory
from asbflow.config import ASBConnectionConfig, ASBConsumerConfig, ParseFailurePolicy
from asbflow.config.defaults import DEFAULT_MAX_MESSAGE_COUNT
from asbflow.consumer.result import (
    ConsumedPayloadFailure,
    ConsumeResult,
    ParsedConsumeResult,
)
from asbflow.entity import ASBEntityClient, ASBEntityClientFactory
from asbflow.shared.asb_ops import ServiceBusPayloadOperations
from asbflow.shared.parsing import (
    DecodedJsonMessage,
    ModelParseResult,
    PydanticModelParser,
)
from asbflow.shared.payloads import PayloadNormalizer, PublishablePayload

if TYPE_CHECKING:
    from asbflow.consumer.failure_handler import ConsumeFailureHandler


@dataclass(frozen=True, slots=True)
class PreparedConsumePayload:
    payload: PublishablePayload
    raw_payload: dict[str, object]
    message_body: str | None


class BaseConsumerStrategy(ABC):
    def __init__(
        self,
        connection: ASBConnectionConfig,
        consumer: ASBConsumerConfig,
        parser: PydanticModelParser | None = None,
        payload_normalizer: PayloadNormalizer | None = None,
        asb_operations: ServiceBusPayloadOperations | None = None,
        client_provider: ASBClientProvider | None = None,
        entity_client: ASBEntityClient | None = None,
    ) -> None:
        self._connection: ASBConnectionConfig = connection
        self._consumer: ASBConsumerConfig = consumer
        self._payload_normalizer: PayloadNormalizer = payload_normalizer or PayloadNormalizer(parser)
        self._asb_operations: ServiceBusPayloadOperations = asb_operations or ServiceBusPayloadOperations()
        self._client_provider: ASBClientProvider = client_provider or ASBClientProviderFactory.create(connection)
        self._entity_client: ASBEntityClient = entity_client or ASBEntityClientFactory.create_for_consumer(consumer)

    @property
    def connection_config(self) -> ASBConnectionConfig:
        return self._connection

    @property
    def consumer_config(self) -> ASBConsumerConfig:
        return self._consumer

    @property
    def parser(self) -> PydanticModelParser | None:
        return self._payload_normalizer.parser

    @property
    def parser_or_raise(self) -> PydanticModelParser:
        return self._payload_normalizer.parser_or_raise

    @property
    def parse_failure_policy(self) -> ParseFailurePolicy:
        return self._consumer.resolved_parse_failure_policy

    def _resolve_parser(self, parser: PydanticModelParser | None) -> PydanticModelParser:
        return self._payload_normalizer.resolve_parser(parser)

    def _build_failure(
        self,
        *,
        error: Exception,
        message_body: str | None,
    ) -> ConsumedPayloadFailure:
        return ConsumedPayloadFailure(error=error, message_body=message_body)

    def _prepare_payload(
        self,
        raw_message: object,
        *,
        parse: bool,
        parser: PydanticModelParser | None,
    ) -> PreparedConsumePayload | ConsumedPayloadFailure:
        decoded: DecodedJsonMessage = self._asb_operations.decode_message(raw_message)
        if decoded.error is not None:
            return self._build_failure(error=decoded.error, message_body=decoded.message_body)

        payload_dict: dict[str, Any] | None = decoded.payload
        if payload_dict is None:
            return self._build_failure(
                error=ValueError("Decoded payload is empty"),
                message_body=decoded.message_body,
            )

        if not parse:
            return PreparedConsumePayload(
                payload=payload_dict,
                raw_payload=payload_dict,
                message_body=decoded.message_body,
            )

        parse_result: ModelParseResult = self._payload_normalizer.parse_dict(payload_dict, parser=parser)
        if parse_result.error is not None:
            return self._build_failure(
                error=parse_result.error,
                message_body=decoded.message_body,
            )

        parsed_payload: BaseModel | None = parse_result.payload
        if parsed_payload is None:
            return self._build_failure(
                error=ValueError("Parsed payload is empty"),
                message_body=decoded.message_body,
            )

        return PreparedConsumePayload(
            payload=parsed_payload,
            raw_payload=payload_dict,
            message_body=decoded.message_body,
        )

    @abstractmethod
    def consume(
        self,
        max_message_count: int,
        *,
        parse: bool = False,
        failure_handler: ConsumeFailureHandler | None = None,
        parser: PydanticModelParser | None = None,
        settle_messages: bool = True,
    ) -> ConsumeResult:
        raise NotImplementedError

    def consume_parsed(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        failure_handler: ConsumeFailureHandler | None = None,
        parser: PydanticModelParser | None = None,
    ) -> ParsedConsumeResult:
        result = self.consume(
            max_message_count=max_message_count,
            parse=True,
            failure_handler=failure_handler,
            parser=parser,
        )
        if isinstance(result, ParsedConsumeResult):
            return result
        raise TypeError("Expected ParsedConsumeResult when parse=True")


__all__ = ["BaseConsumerStrategy", "PreparedConsumePayload"]
