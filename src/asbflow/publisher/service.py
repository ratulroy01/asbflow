from __future__ import annotations

from asbflow.config import (
    DEFAULT_CHUNK_SIZE,
    ASBConnectionConfig,
    ASBPublisherConfig,
)
from asbflow.config.defaults import get_asbflow_logger
from asbflow.config.message import MessageConfigInput
from asbflow.exceptions import PublishError
from asbflow.shared.parsing import PydanticModelParser

from .base import BasePublisherStrategy, PublishablePayload, PublishInput
from .factory import PublisherFactory, PublishExecutionMode

LOGGER = get_asbflow_logger(__name__)


class ASBPublisher:
    """Publish payloads to Azure Service Bus in a model-agnostic way."""

    def __init__(
        self,
        connection: ASBConnectionConfig,
        publisher: ASBPublisherConfig,
        message: MessageConfigInput | None = None,
        execution_mode: PublishExecutionMode | str = PublishExecutionMode.SEQUENTIAL,
        parser: PydanticModelParser | None = None,
        strategy: BasePublisherStrategy | None = None,
    ) -> None:
        """Initialize a publisher service.

        Parameters
        ----------
        connection : ASBConnectionConfig
            Azure Service Bus connection configuration.
        publisher : ASBPublisherConfig
            Topic sender configuration.
        message : MessageConfigInput | None
            Optional default Service Bus message metadata.
        execution_mode : PublishExecutionMode | str
            Strategy used to send messages/batches.
        parser : PydanticModelParser | None
            Default parser used when ``parse=True``.
        strategy : BasePublisherStrategy | None
            Optional pre-built strategy. If provided, strategy creation is skipped.
        """
        self._execution_mode: PublishExecutionMode = PublishExecutionMode.parse(execution_mode)

        self._strategy: BasePublisherStrategy = strategy or PublisherFactory.create_strategy(
            self._execution_mode,
            connection=connection,
            publisher=publisher,
            message=message,
            parser=parser,
        )

    @property
    def connection_config(self) -> ASBConnectionConfig:
        """Return the connection configuration used by this publisher."""
        return self._strategy.connection_config

    @property
    def publisher_config(self) -> ASBPublisherConfig:
        """Return the topic sender configuration used by this publisher."""
        return self._strategy.publisher_config

    @property
    def message_config(self) -> MessageConfigInput:
        """Return the default Service Bus message configuration."""
        return self._strategy.message_config

    @property
    def parser(self) -> PydanticModelParser | None:
        """Return the default parser used for parsed publish operations."""
        return self._strategy.parser

    @property
    def execution_mode(self) -> PublishExecutionMode:
        """Return the configured publish execution mode."""
        return self._execution_mode

    @staticmethod
    def _raise_publish_error(*, operation: str, error: Exception) -> None:
        raise PublishError(operation=operation, error=error) from error

    def publish_message(
        self,
        payload: PublishablePayload,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        message: MessageConfigInput | None = None,
    ) -> None:
        """Publish a single payload.

        Parameters
        ----------
        payload : PublishInput
            Payload dictionary or pydantic model.
        parse : bool
            If ``True``, parse dictionaries before publication.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        message : MessageConfigInput | None
            Optional message-config override for this call.

        Raises
        ------
        PublishError
            If publication fails.
        """
        LOGGER.debug(
            "Publish-message requested (parse=%s, override_parser=%s, override_message=%s)",
            parse,
            parser is not None,
            message is not None,
        )
        try:
            self._strategy.publish_message(payload, parse=parse, parser=parser, message=message)
            LOGGER.info("Publish-message completed")
        except Exception as exc:
            LOGGER.exception(
                "Publish-message failed (parse=%s, override_parser=%s, override_message=%s)",
                parse,
                parser is not None,
                message is not None,
            )
            self._raise_publish_error(operation="publish_message", error=exc)

    def publish_message_parsed(
        self,
        payload: PublishablePayload,
        *,
        parser: PydanticModelParser | None = None,
        message: MessageConfigInput | None = None,
    ) -> None:
        """Publish a single payload with parsing enabled.

        Parameters
        ----------
        payload : PublishInput
            Payload dictionary or pydantic model.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        message : MessageConfigInput | None
            Optional message-config override for this call.
        """
        self.publish_message(
            payload,
            parse=True,
            parser=parser,
            message=message,
        )

    def publish_batch(
        self,
        payloads: list[PublishablePayload],
        *,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        message: MessageConfigInput | None = None,
    ) -> None:
        """Publish a batch of payloads.

        Parameters
        ----------
        payloads : list[PublishablePayload]
            Payload dictionaries or pydantic models.
        chunk_size : int | None
            Optional maximum items per chunk before SDK batch packing.
        parse : bool
            If ``True``, parse dictionaries before publication.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        message : MessageConfigInput | None
            Optional message-config override for this call.

        Raises
        ------
        PublishError
            If publication fails.
        """
        LOGGER.info(
            "Publish-batch requested (payload_count=%s, chunk_size=%s, parse=%s, override_parser=%s, override_message=%s)",
            len(payloads),
            chunk_size,
            parse,
            parser is not None,
            message is not None,
        )
        try:
            self._strategy.publish_batch(
                payloads,
                chunk_size=chunk_size,
                parse=parse,
                parser=parser,
                message=message,
            )
            LOGGER.info(
                "Publish-batch completed (payload_count=%s)",
                len(payloads),
            )
        except Exception as exc:
            LOGGER.exception(
                "Publish-batch failed (payload_count=%s, chunk_size=%s, parse=%s, override_parser=%s, override_message=%s)",
                len(payloads),
                chunk_size,
                parse,
                parser is not None,
                message is not None,
            )
            self._raise_publish_error(operation="publish_batch", error=exc)

    def publish_batch_parsed(
        self,
        payloads: list[PublishablePayload],
        *,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        parser: PydanticModelParser | None = None,
        message: MessageConfigInput | None = None,
    ) -> None:
        """Publish a batch of payloads with parsing enabled.

        Parameters
        ----------
        payloads : list[PublishablePayload]
            Payload dictionaries or pydantic models.
        chunk_size : int | None
            Optional maximum items per chunk before SDK batch packing.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        message : MessageConfigInput | None
            Optional message-config override for this call.
        """
        self.publish_batch(
            payloads,
            chunk_size=chunk_size,
            parse=True,
            parser=parser,
            message=message,
        )

    def publish(
        self,
        payload: PublishInput,
        *,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
        message: MessageConfigInput | None = None,
    ) -> None:
        """Publish one payload or a list of payloads.

        Parameters
        ----------
        payload : PublishInput
            Single payload or list of payloads.
        chunk_size : int | None
            Optional maximum items per chunk for batch publication.
        parse : bool
            If ``True``, parse dictionaries before publication.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        message : MessageConfigInput | None
            Optional message-config override for this call.

        Raises
        ------
        PublishError
            If publication fails.
        """
        payload_count = len(payload) if isinstance(payload, list) else 1
        LOGGER.info(
            "Publish requested (payload_count=%s, chunk_size=%s, parse=%s, override_parser=%s, override_message=%s)",
            payload_count,
            chunk_size,
            parse,
            parser is not None,
            message is not None,
        )
        try:
            self._strategy.publish(
                payload,
                chunk_size=chunk_size,
                parse=parse,
                parser=parser,
                message=message,
            )
            LOGGER.info("Publish completed (payload_count=%s)", payload_count)
        except Exception as exc:
            LOGGER.exception(
                "Publish failed (payload_count=%s, chunk_size=%s, parse=%s, override_parser=%s, override_message=%s)",
                payload_count,
                chunk_size,
                parse,
                parser is not None,
                message is not None,
            )
            self._raise_publish_error(operation="publish", error=exc)

    def publish_parsed(
        self,
        payload: PublishInput,
        *,
        chunk_size: int | None = DEFAULT_CHUNK_SIZE,
        parser: PydanticModelParser | None = None,
        message: MessageConfigInput | None = None,
    ) -> None:
        """Publish one payload or a list of payloads with parsing enabled.

        Parameters
        ----------
        payload : PublishInput
            Single payload or list of payloads.
        chunk_size : int | None
            Optional maximum items per chunk for batch publication.
        parser : PydanticModelParser | None
            Optional parser overriding the service default for this call.
        message : MessageConfigInput | None
            Optional message-config override for this call.
        """
        self.publish(
            payload,
            chunk_size=chunk_size,
            parse=True,
            parser=parser,
            message=message,
        )


__all__ = [
    "ASBPublisher",
    "PublishExecutionMode",
    "PublishInput",
    "PublishablePayload",
]
