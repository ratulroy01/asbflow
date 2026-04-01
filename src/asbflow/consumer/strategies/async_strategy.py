from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from threading import Thread
from typing import Any

from overrides import override

from asbflow.config.defaults import DEFAULT_MAX_MESSAGE_COUNT, get_asbflow_logger
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


class AsyncConsumerStrategy(BaseConsumerStrategy):
    @staticmethod
    def _run_coroutine_sync(coroutine: Coroutine[object, object, object]) -> object:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)

        result_holder: dict[str, object] = {}
        error_holder: dict[str, BaseException] = {}

        def _runner() -> None:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                result_holder["result"] = loop.run_until_complete(coroutine)
            except BaseException as exc:  # pragma: no cover
                error_holder["error"] = exc
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        worker = Thread(target=_runner, daemon=True)
        worker.start()
        worker.join()

        if "error" in error_holder:
            raise error_holder["error"]
        return result_holder["result"]

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
            "Async strategy sync-wrapper consume start (max_message_count=%s, parse=%s, settle_messages=%s)",
            max_message_count,
            parse,
            settle_messages,
        )
        result = self._run_coroutine_sync(
            self.aconsume(
                max_message_count=max_message_count,
                parse=parse,
                failure_handler=failure_handler,
                parser=parser,
                settle_messages=settle_messages,
            )
        )
        if isinstance(result, (RawConsumeResult, ParsedConsumeResult)):
            LOGGER.debug(
                "Async strategy sync-wrapper consume completed (parse=%s, settle_messages=%s, successes=%s, failures=%s)",
                parse,
                settle_messages,
                len(result.successes),
                len(result.failures),
            )
            return result
        raise TypeError("Unexpected consume result type")

    async def aconsume(
        self,
        max_message_count: int = DEFAULT_MAX_MESSAGE_COUNT,
        *,
        parse: bool = False,
        failure_handler: ConsumeFailureHandler | None = None,
        parser: PydanticModelParser | None = None,
        settle_messages: bool = True,
    ) -> ConsumeResult:
        LOGGER.debug(
            "Async strategy consume start (max_message_count=%s, parse=%s, settle_messages=%s)",
            max_message_count,
            parse,
            settle_messages,
        )
        effective_failure_handler: ConsumeFailureHandler = failure_handler or ConsumeFailureHandler()
        effective_parser: PydanticModelParser | None = self._resolve_parser(parser) if parse else None

        raw_messages: list[RawConsumedMessage] = []
        parsed_messages: list[object] = []
        errors: list[ConsumedPayloadFailure] = []

        async_client = await self._client_provider.create_async_client()
        async with async_client as client:
            async with self._entity_client.get_async_receiver(client, self._consumer) as receiver:
                messages: Any = await receiver.receive_messages(max_message_count=max_message_count)
                LOGGER.debug("Async strategy consume received messages=%s", len(messages))

                for raw_message in messages:
                    prepared: PreparedConsumePayload | ConsumedPayloadFailure = self._prepare_payload(
                        raw_message,
                        parse=parse,
                        parser=effective_parser,
                    )
                    if isinstance(prepared, ConsumedPayloadFailure):
                        errors.append(prepared)
                        if settle_messages:
                            await effective_failure_handler.asettle_failed_message(
                                receiver,
                                raw_message,
                                policy=self.parse_failure_policy,
                            )
                        continue

                    if settle_messages:
                        try:
                            await receiver.complete_message(raw_message)
                        except Exception as exc:
                            await effective_failure_handler.ahandle_transient_consume_error(
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
                "Async strategy consume completed (parse=%s, settle_messages=%s, successes=%s, failures=%s)",
                True,
                settle_messages,
                len(result.successes),
                len(result.failures),
            )
            return result

        result = RawConsumeResult(raw_messages=raw_messages, errors=errors)
        LOGGER.debug(
            "Async strategy consume completed (parse=%s, settle_messages=%s, successes=%s, failures=%s)",
            False,
            settle_messages,
            len(result.successes),
            len(result.failures),
        )
        return result


__all__ = ["AsyncConsumerStrategy"]
