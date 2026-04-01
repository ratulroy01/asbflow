from __future__ import annotations

from asbflow.config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_DLQ_PURGE_MAX_MESSAGE_COUNT,
    DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
    ASBConnectionConfig,
    ASBConsumerConfig,
    ASBPublisherConfig,
    get_asbflow_logger,
)
from asbflow.consumer import ASBConsumer
from asbflow.consumer.result import ConsumeResult, ParsedConsumeResult, RawConsumeResult
from asbflow.dlq.protocols import _ConsumerLike, _PublisherLike
from asbflow.dlq.result import (
    DLQParsedReadResult,
    DLQPurgeResult,
    DLQRawReadResult,
    DLQReadResult,
    DLQRedriveResult,
)
from asbflow.exceptions import DLQError, DLQPublisherNotConfiguredError
from asbflow.publisher import ASBPublisher
from asbflow.shared.payloads import PublishablePayload

LOGGER = get_asbflow_logger(__name__)


class ASBDLQManager:
    """Manage dead-letter queue operations for an ASB subscription."""

    def __init__(
        self,
        consumer: ASBConsumer | _ConsumerLike,
        publisher: ASBPublisher | _PublisherLike | None = None,
        raise_on_error: bool = True,
    ) -> None:
        """Initialize a DLQ manager.

        Parameters
        ----------
        consumer : ASBConsumer | _ConsumerLike
            Consumer service or compatible consumer-like object.
        publisher : ASBPublisher | _PublisherLike | None
            Optional publisher service or compatible publisher-like object.
        raise_on_error : bool
            Default raise policy for DLQ operations.
        """
        self._raise_on_error: bool = raise_on_error
        self._consumer: ASBConsumer | _ConsumerLike = consumer
        self._publisher: ASBPublisher | _PublisherLike | None = publisher

    @property
    def connection_config(self) -> ASBConnectionConfig | None:
        """Return the shared ASB connection configuration when available."""
        connection = getattr(self._consumer, "connection_config", None)
        if connection is not None:
            return connection
        return getattr(self._publisher, "connection_config", None)

    @property
    def consumer_config(self) -> ASBConsumerConfig | None:
        """Return the consumer configuration when available."""
        return getattr(self._consumer, "consumer_config", None)

    @property
    def publisher_config(self) -> ASBPublisherConfig | None:
        """Return the publisher configuration when available."""
        return getattr(self._publisher, "publisher_config", None)

    @property
    def raise_on_error(self) -> bool:
        """Return the default raise-on-error policy."""
        return self._raise_on_error

    def _resolve_raise_on_error(self, override: bool | None) -> bool:
        return self._raise_on_error if override is None else override

    def consume(
        self,
        max_message_count: int = DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
        parse: bool = False,
        raise_on_error: bool | None = None,
        settle_messages: bool = True,
    ) -> DLQReadResult:
        """Consume one DLQ batch.

        Parameters
        ----------
        max_message_count : int
            Maximum number of messages requested in one receive call.
        parse : bool
            If ``True``, parse payloads before returning them.
        raise_on_error : bool | None
            Optional override for raise policy.
        settle_messages : bool
            If ``True``, settle messages according to consume outcomes.
            If ``False``, leave messages unsettled.

        Returns
        -------
        DLQReadResult
            Parsed or raw DLQ read result.

        Raises
        ------
        DLQError
            If message-level failures are collected and raise policy is enabled.
        """
        resolved_raise_on_error: bool = self._resolve_raise_on_error(raise_on_error)
        consumed: ConsumeResult = self._consumer.consume(
            max_message_count=max_message_count,
            parse=parse,
            raise_on_error=False,
            settle_messages=settle_messages,
        )

        if parse:
            if not isinstance(consumed, ParsedConsumeResult):
                raise TypeError("Expected ParsedConsumeResult when parse=True")

            result_parsed = DLQParsedReadResult(
                parsed=list(consumed.successes),
                failed_payloads=[failure.message_body or "" for failure in consumed.failures],
            )
            if resolved_raise_on_error and result_parsed.failed:
                raise DLQError(operation="read", result=result_parsed)
            return result_parsed

        if not isinstance(consumed, RawConsumeResult):
            raise TypeError("Expected RawConsumeResult when parse=False")

        result_raw = DLQRawReadResult(
            messages=[dict(message) for message in consumed.successes],
            failed_payloads=[failure.message_body or "" for failure in consumed.failures],
        )
        if resolved_raise_on_error and result_raw.failed:
            raise DLQError(operation="read", result=result_raw)
        return result_raw

    def consume_parsed(
        self,
        max_message_count: int = DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
        raise_on_error: bool | None = None,
    ) -> DLQParsedReadResult:
        """Consume one DLQ batch with parsing enabled."""
        result: DLQReadResult = self.consume(
            max_message_count=max_message_count,
            parse=True,
            raise_on_error=raise_on_error,
            settle_messages=True,
        )
        if not isinstance(result, DLQParsedReadResult):
            raise TypeError("Expected DLQParsedReadResult when parse=True")
        return result

    def read(
        self,
        max_message_count: int = DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
        parse: bool = False,
        raise_on_error: bool | None = None,
    ) -> DLQReadResult:
        """Read one DLQ batch leaving messages unsettled."""
        return self.consume(
            max_message_count=max_message_count,
            parse=parse,
            raise_on_error=raise_on_error,
            settle_messages=False,
        )

    def read_parsed(
        self,
        max_message_count: int = DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
        raise_on_error: bool | None = None,
    ) -> DLQParsedReadResult:
        """Read one DLQ batch with parsing enabled, without settling messages."""
        result: DLQReadResult = self.read(
            max_message_count=max_message_count,
            parse=True,
            raise_on_error=raise_on_error,
        )
        if not isinstance(result, DLQParsedReadResult):
            raise TypeError("Expected DLQParsedReadResult when parse=True")
        return result

    def redrive(
        self,
        max_message_count: int = DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        parse: bool = False,
        raise_on_error: bool | None = None,
    ) -> DLQRedriveResult:
        """Republish one DLQ batch to the active topic.

        Parameters
        ----------
        max_message_count : int
            Maximum number of DLQ messages requested in one receive call.
        chunk_size : int | None
            Optional publisher chunk size.
        parse : bool
            If ``True``, redrive only successfully parsed payloads.
        raise_on_error : bool | None
            Optional override for raise policy.

        Returns
        -------
        DLQRedriveResult
            Redrive operation summary.

        Raises
        ------
        DLQPublisherNotConfiguredError
            If no publisher is configured.
        DLQError
            If the redrive operation completes with failures and raise policy is enabled.
        """
        resolved_raise_on_error = self._resolve_raise_on_error(raise_on_error)
        if self._publisher is None:
            raise DLQPublisherNotConfiguredError(
                "redrive requires a configured publisher. "
                "Instantiate ASBDLQManager with publisher=ASBPublisher(...) or ASBPublisherConfig(...)."
            )

        consumed: ConsumeResult = self._consumer.consume(
            max_message_count=max_message_count,
            parse=parse,
            raise_on_error=False,
        )

        if parse and not isinstance(consumed, ParsedConsumeResult):
            raise TypeError("Expected ParsedConsumeResult when parse=True")
        if not parse and not isinstance(consumed, RawConsumeResult):
            raise TypeError("Expected RawConsumeResult when parse=False")

        payloads_to_publish: list[PublishablePayload] = list(consumed.successes)
        parse_failed: int = len(consumed.failures)
        republished: int = 0
        publish_failed: int = 0

        for payload in payloads_to_publish:
            try:
                self._publisher.publish(payload, chunk_size=chunk_size)
                republished += 1
            except Exception:
                LOGGER.exception("Failed to republish DLQ message")
                publish_failed += 1

        result = DLQRedriveResult(
            republished=republished,
            parse_failed=parse_failed,
            publish_failed=publish_failed,
        )
        if resolved_raise_on_error and result.failed:
            raise DLQError(operation="redrive", result=result)
        return result

    def redrive_parsed(
        self,
        max_message_count: int = DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        raise_on_error: bool | None = None,
    ) -> DLQRedriveResult:
        """Republish one DLQ batch with parsing enabled."""
        return self.redrive(
            max_message_count=max_message_count,
            chunk_size=chunk_size,
            parse=True,
            raise_on_error=raise_on_error,
        )

    def purge(
        self,
        max_message_count: int = DEFAULT_DLQ_PURGE_MAX_MESSAGE_COUNT,
        raise_on_error: bool | None = None,
    ) -> DLQPurgeResult:
        """Purge one DLQ batch.

        Parameters
        ----------
        max_message_count : int
            Maximum number of DLQ messages requested in one receive call.
        raise_on_error : bool | None
            Optional override for raise policy.

        Returns
        -------
        DLQPurgeResult
            Purge operation summary.

        Raises
        ------
        DLQError
            If purge operation completes with failures and raise policy is enabled.
        """
        resolved_raise_on_error = self._resolve_raise_on_error(raise_on_error)
        consumed: ConsumeResult = self._consumer.consume(
            max_message_count=max_message_count,
            parse=False,
            raise_on_error=False,
        )
        if not isinstance(consumed, RawConsumeResult):
            raise TypeError("Expected RawConsumeResult when purge consumes raw messages")

        purge_result = DLQPurgeResult(
            purged=len(consumed.successes),
            errors=len(consumed.failures),
        )
        if resolved_raise_on_error and purge_result.failed:
            raise DLQError(operation="purge", result=purge_result)
        return purge_result


__all__ = ["ASBDLQManager"]
