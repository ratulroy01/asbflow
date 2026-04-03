from __future__ import annotations

from typing import Any

from asbflow.config import ASBConnectionConfig, ASBConsumerConfig, ParseFailurePolicy
from asbflow.config.defaults import DEFAULT_MAX_MESSAGE_COUNT, get_asbflow_logger
from asbflow.shared.parsing import PydanticModelParser
from asbflow.shared.resolution import PropertyResolver

from .base import BaseConsumerStrategy
from .factory import ConsumeExecutionMode, ConsumerFactory
from .failure_handler import ConsumeFailureHandler
from .result import (
    ConsumedPayloadFailure,
    ConsumeError,
    ConsumeResult,
    ParsedConsumeResult,
    RawConsumedMessage,
    RawConsumeResult,
)
from .strategies import AsyncConsumerStrategy

LOGGER = get_asbflow_logger(__name__)


class ASBConsumer:
    """Consume messages from an Azure Service Bus subscription."""

    def __init__(
        self,
        connection: ASBConnectionConfig,
        consumer: ASBConsumerConfig,
        execution_mode: ConsumeExecutionMode | str = ConsumeExecutionMode.SEQUENTIAL,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool = True,
        strategy: BaseConsumerStrategy | None = None,
    ) -> None:
        """Initialize a consumer service.

        Parameters
        ----------
        connection : ASBConnectionConfig
            Azure Service Bus connection configuration.
        consumer : ASBConsumerConfig
            Subscription receiver configuration.
        execution_mode : ConsumeExecutionMode | str
            Strategy used to receive/process messages.
        parser : PydanticModelParser | None
            Default parser used when ``parse=True``.
        raise_on_error : bool
            Default raise policy for consume/read methods.
        strategy : BaseConsumerStrategy | None
            Optional pre-built strategy. If provided, strategy creation is skipped.
        """
        self._execution_mode: ConsumeExecutionMode = ConsumeExecutionMode.parse(execution_mode)
        self._failure_handler: ConsumeFailureHandler = ConsumeFailureHandler()
        self._raise_on_error_resolver: PropertyResolver[bool] = PropertyResolver(raise_on_error)

        self._strategy: BaseConsumerStrategy = strategy or ConsumerFactory.create_strategy(
            self._execution_mode,
            connection=connection,
            consumer=consumer,
            parser=parser,
        )

    @property
    def connection_config(self) -> ASBConnectionConfig:
        """Return the connection configuration used by this consumer."""
        return self._strategy.connection_config

    @property
    def consumer_config(self) -> ASBConsumerConfig:
        """Return the subscription configuration used by this consumer."""
        return self._strategy.consumer_config

    @property
    def parser(self) -> PydanticModelParser | None:
        """Return the default parser used for parsed consume operations."""
        return self._strategy.parser

    @property
    def execution_mode(self) -> ConsumeExecutionMode:
        """Return the configured consume execution mode."""
        return self._execution_mode

    @property
    def raise_on_error(self) -> bool:
        """Return the default raise-on-error policy."""
        return self._raise_on_error_resolver.default

    def consume(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool | None = None,
        settle_messages: bool = True,
    ) -> ConsumeResult:
        """Consume one batch of messages.

        Parameters
        ----------
        max_message_count : int
            Maximum number of messages requested in one receive call.
        parse : bool
            If ``True``, parse payloads using a pydantic parser.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        raise_on_error : bool | None
            Optional override for raise policy.
        settle_messages : bool
            If ``True``, settle received messages according to success/failure outcome.
            If ``False``, leave all messages unsettled.

        Returns
        -------
        ConsumeResult
            Parsed or raw consume result, depending on ``parse``.

        Raises
        ------
        ConsumeError
            If message-level failures are collected and raise policy is enabled.
        """
        resolved_raise_on_error: bool = self._raise_on_error_resolver.resolve(raise_on_error)
        LOGGER.debug(
            "Consume requested (max_message_count=%s, parse=%s, settle_messages=%s, override_parser=%s, raise_on_error=%s)",
            max_message_count,
            parse,
            settle_messages,
            parser is not None,
            resolved_raise_on_error,
        )
        result: ConsumeResult = self._strategy.consume(
            max_message_count=max_message_count,
            parse=parse,
            failure_handler=self._failure_handler,
            parser=parser,
            settle_messages=settle_messages,
        )
        LOGGER.debug(
            "Consume completed (parse=%s, settle_messages=%s, successes=%s, failures=%s)",
            parse,
            settle_messages,
            len(result.successes),
            len(result.failures),
        )
        if resolved_raise_on_error and result.failed:
            LOGGER.warning(
                "Consume failed with collected message errors (failures=%s, parse=%s)",
                len(result.failures),
                parse,
            )
            raise ConsumeError(result)
        return result

    def read(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool | None = None,
    ) -> ConsumeResult:
        """Read one batch without settling messages.

        Parameters
        ----------
        max_message_count : int
            Maximum number of messages requested in one receive call.
        parse : bool
            If ``True``, parse payloads using a pydantic parser.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        raise_on_error : bool | None
            Optional override for raise policy.

        Returns
        -------
        ConsumeResult
            Parsed or raw read result.
        """
        return self.consume(
            max_message_count=max_message_count,
            parse=parse,
            parser=parser,
            raise_on_error=raise_on_error,
            settle_messages=False,
        )

    def consume_parsed(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        raise_on_error: bool | None = None,
        parser: PydanticModelParser | None = None,
    ) -> ParsedConsumeResult:
        """Consume one batch with parsing enabled."""
        result = self.consume(
            max_message_count=max_message_count,
            parse=True,
            parser=parser,
            raise_on_error=raise_on_error,
        )
        if not isinstance(result, ParsedConsumeResult):
            raise TypeError("Expected ParsedConsumeResult when parse=True")
        return result

    def consume_all(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        raise_on_error: bool | None = None,
        parser: PydanticModelParser | None = None,
    ) -> ConsumeResult:
        """Consume all currently available messages in repeated batches.

        Parameters
        ----------
        max_message_count : int
            Maximum number of messages requested in each receive call.
        parse : bool
            If ``True``, parse payloads using a pydantic parser.
        raise_on_error : bool | None
            Optional override for raise policy.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.

        Returns
        -------
        ConsumeResult
            Aggregate parsed or raw consume result.

        Raises
        ------
        RuntimeError
            If no progress is possible with ``leave_unsettled`` and only failures are received.
        ConsumeError
            If message-level failures are collected and raise policy is enabled.
        """
        resolved_raise_on_error = self._raise_on_error_resolver.resolve(raise_on_error)
        LOGGER.info(
            "Consume-all requested (max_message_count=%s, parse=%s, override_parser=%s, raise_on_error=%s)",
            max_message_count,
            parse,
            parser is not None,
            resolved_raise_on_error,
        )

        if parse:
            parsed_messages: list[Any] = []
            errors: list[ConsumedPayloadFailure] = []

            while True:
                batch_result: ConsumeResult = self.consume(
                    max_message_count=max_message_count,
                    parse=True,
                    raise_on_error=False,
                    parser=parser,
                )
                if not isinstance(batch_result, ParsedConsumeResult):
                    raise TypeError("Expected ParsedConsumeResult when parse=True")
                if not batch_result.successes and not batch_result.failures:
                    break

                if (
                    not batch_result.successes
                    and batch_result.failures
                    and self._strategy.parse_failure_policy is ParseFailurePolicy.LEAVE_UNSETTLED
                ):
                    raise RuntimeError(
                        "consume_all cannot progress with parse_failure_policy='leave_unsettled' "
                        "when only failures are received"
                    )

                parsed_messages.extend(batch_result.parsed_messages)
                errors.extend(batch_result.failures)

            result = ParsedConsumeResult(parsed_messages=parsed_messages, errors=errors)
            if resolved_raise_on_error and result.failed:
                raise ConsumeError(result)
            return result

        raw_messages: list[RawConsumedMessage] = []
        errors: list[ConsumedPayloadFailure] = []

        while True:
            batch_result: ConsumeResult = self.consume(
                max_message_count=max_message_count,
                parse=False,
                raise_on_error=False,
                parser=parser,
            )
            if not isinstance(batch_result, RawConsumeResult):
                raise TypeError("Expected RawConsumeResult when parse=False")
            if not batch_result.successes and not batch_result.failures:
                break

            raw_messages.extend(batch_result.raw_messages)
            errors.extend(batch_result.failures)

        result = RawConsumeResult(raw_messages=raw_messages, errors=errors)
        if resolved_raise_on_error and result.failed:
            raise ConsumeError(result)
        return result

    async def aconsume(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        raise_on_error: bool | None = None,
        settle_messages: bool = True,
    ) -> ConsumeResult:
        """Asynchronously consume one batch of messages."""
        if not isinstance(self._strategy, AsyncConsumerStrategy):
            raise ValueError("aconsume is available only when execution_mode is 'async'")

        resolved_raise_on_error: bool = self._raise_on_error_resolver.resolve(raise_on_error)
        result: ConsumeResult = await self._strategy.aconsume(
            max_message_count=max_message_count,
            parse=parse,
            failure_handler=self._failure_handler,
            parser=parser,
            settle_messages=settle_messages,
        )
        if resolved_raise_on_error and result.failed:
            raise ConsumeError(result)
        return result

    async def aconsume_parsed(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        raise_on_error: bool | None = None,
        parser: PydanticModelParser | None = None,
    ) -> ParsedConsumeResult:
        """Asynchronously consume one batch with parsing enabled."""
        result: ConsumeResult = await self.aconsume(
            max_message_count=max_message_count,
            parse=True,
            parser=parser,
            raise_on_error=raise_on_error,
        )
        if not isinstance(result, ParsedConsumeResult):
            raise TypeError("Expected ParsedConsumeResult when parse=True")
        return result

    async def aconsume_all(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        raise_on_error: bool | None = None,
        parser: PydanticModelParser | None = None,
    ) -> ConsumeResult:
        """Asynchronously consume all currently available messages."""
        if not isinstance(self._strategy, AsyncConsumerStrategy):
            raise ValueError("aconsume_all is available only when execution_mode is 'async'")

        resolved_raise_on_error: bool = self._raise_on_error_resolver.resolve(raise_on_error)

        if parse:
            parsed_messages: list[Any] = []
            errors: list[ConsumedPayloadFailure] = []

            while True:
                batch_result: ConsumeResult = await self.aconsume(
                    max_message_count=max_message_count,
                    parse=True,
                    raise_on_error=False,
                    parser=parser,
                )
                if not isinstance(batch_result, ParsedConsumeResult):
                    raise TypeError("Expected ParsedConsumeResult when parse=True")
                if not batch_result.successes and not batch_result.failures:
                    break

                if (
                    not batch_result.successes
                    and batch_result.failures
                    and self._strategy.parse_failure_policy is ParseFailurePolicy.LEAVE_UNSETTLED
                ):
                    raise RuntimeError(
                        "aconsume_all cannot progress with parse_failure_policy='leave_unsettled' "
                        "when only failures are received"
                    )

                parsed_messages.extend(batch_result.parsed_messages)
                errors.extend(batch_result.failures)

            result = ParsedConsumeResult(parsed_messages=parsed_messages, errors=errors)
            if resolved_raise_on_error and result.failed:
                raise ConsumeError(result)
            return result

        raw_messages: list[RawConsumedMessage] = []
        errors: list[ConsumedPayloadFailure] = []

        while True:
            batch_result: ConsumeResult = await self.aconsume(
                max_message_count=max_message_count,
                parse=False,
                raise_on_error=False,
                parser=parser,
            )
            if not isinstance(batch_result, RawConsumeResult):
                raise TypeError("Expected RawConsumeResult when parse=False")
            if not batch_result.successes and not batch_result.failures:
                break

            raw_messages.extend(batch_result.raw_messages)
            errors.extend(batch_result.failures)

        result = RawConsumeResult(raw_messages=raw_messages, errors=errors)
        if resolved_raise_on_error and result.failed:
            raise ConsumeError(result)
        return result


__all__ = ["ASBConsumer", "ConsumeExecutionMode"]
