from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from overrides import override

from asbflow.config.defaults import (
    DEFAULT_CONSUME_THREAD_POOL_MAX_WORKERS,
    DEFAULT_MAX_MESSAGE_COUNT,
    get_asbflow_logger,
)
from asbflow.consumer.failure_handler import ConsumeFailureHandler
from asbflow.consumer.result import (
    ConsumedPayloadFailure,
    ConsumeResult,
    ParsedConsumeResult,
    RawConsumedMessage,
    RawConsumeResult,
)
from asbflow.shared.parsing import PydanticModelParser

from ..base import BaseConsumerStrategy, PreparedConsumePayload

LOGGER = get_asbflow_logger(__name__)


class ThreadPoolConsumerStrategy(BaseConsumerStrategy):
    @override
    def consume(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        failure_handler: ConsumeFailureHandler | None = None,
        parser: PydanticModelParser | None = None,
        settle_messages: bool = True,
    ) -> ConsumeResult:
        LOGGER.debug(
            "Thread-pool consume start (max_message_count=%s, parse=%s, settle_messages=%s)",
            max_message_count,
            parse,
            settle_messages,
        )
        effective_failure_handler: ConsumeFailureHandler = failure_handler or ConsumeFailureHandler()
        effective_parser: PydanticModelParser | None = self._resolve_parser(parser) if parse else None

        raw_messages: list[RawConsumedMessage] = []
        parsed_messages: list[object] = []
        errors: list[ConsumedPayloadFailure] = []

        with self._client_provider.create_sync_client() as client:
            with self._entity_client.get_sync_receiver(client, self._consumer) as receiver:
                messages: Any = receiver.receive_messages(max_message_count=max_message_count)
                LOGGER.debug("Thread-pool consume received messages=%s", len(messages))

                with ThreadPoolExecutor(
                    max_workers=min(
                        max(len(messages), 1),
                        DEFAULT_CONSUME_THREAD_POOL_MAX_WORKERS,
                    )
                ) as executor:
                    future_map: dict[Future[PreparedConsumePayload | ConsumedPayloadFailure], Any] = {
                        executor.submit(
                            self._prepare_payload,
                            raw_message,
                            parse=parse,
                            parser=effective_parser,
                        ): raw_message
                        for raw_message in messages
                    }

                    for future, raw_message in future_map.items():
                        prepared: PreparedConsumePayload | ConsumedPayloadFailure = future.result()
                        if isinstance(prepared, ConsumedPayloadFailure):
                            errors.append(prepared)
                            if settle_messages:
                                effective_failure_handler.settle_failed_message(
                                    receiver,
                                    raw_message,
                                    policy=self.parse_failure_policy,
                                )
                            continue

                        if settle_messages:
                            try:
                                receiver.complete_message(raw_message)
                            except Exception as exc:
                                effective_failure_handler.handle_transient_consume_error(
                                    receiver,
                                    raw_message,
                                    exc,
                                    errors,
                                )
                                continue

                        if parse:
                            parsed_messages.append(prepared.payload)
                        else:
                            raw_messages.append(
                                RawConsumedMessage(
                                    payload=prepared.raw_payload,
                                    message_body=prepared.message_body,
                                )
                            )

        if parse:
            result = ParsedConsumeResult(parsed_messages=parsed_messages, errors=errors)
            LOGGER.debug(
                "Thread-pool consume completed (parse=%s, settle_messages=%s, successes=%s, failures=%s)",
                True,
                settle_messages,
                len(result.successes),
                len(result.failures),
            )
            return result

        result = RawConsumeResult(raw_messages=raw_messages, errors=errors)
        LOGGER.debug(
            "Thread-pool consume completed (parse=%s, settle_messages=%s, successes=%s, failures=%s)",
            False,
            settle_messages,
            len(result.successes),
            len(result.failures),
        )
        return result


__all__ = ["ThreadPoolConsumerStrategy"]
