from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from threading import Thread

from overrides import override

from asbflow.config.defaults import get_asbflow_logger
from asbflow.shared.parsing import PydanticModelParser
from asbflow.shared.sdk import ASBAsyncClient, ASBMessageType, load_asb_message_type

from ..base import BasePublisherStrategy, PublishablePayload

LOGGER = get_asbflow_logger(__name__)


class AsyncPublisherStrategy(BasePublisherStrategy):
    @override
    def publish_batch(
        self,
        payloads: list[PublishablePayload],
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        LOGGER.debug(
            "Async publish-batch sync-wrapper start (payload_count=%s, chunk_size=%s, parse=%s)",
            len(payloads),
            chunk_size,
            parse,
        )
        self._run_coroutine_sync(
            self._publish_batch_with_async_sdk(
                payloads,
                chunk_size=chunk_size,
                parse=parse,
                parser=parser,
            )
        )
        LOGGER.debug(
            "Async publish-batch sync-wrapper completed (payload_count=%s)",
            len(payloads),
        )

    @staticmethod
    def _run_coroutine_sync(coroutine: Coroutine[object, object, None]) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coroutine)
            return

        error_holder: dict[str, BaseException] = {}

        def _runner() -> None:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                loop.run_until_complete(coroutine)
            except BaseException as exc:  # pragma: no cover - re-raised in caller
                error_holder["error"] = exc
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        worker = Thread(target=_runner, daemon=True)
        worker.start()
        worker.join()

        if "error" in error_holder:
            raise error_holder["error"]

    async def _publish_batch_with_async_sdk(
        self,
        payloads: list[PublishablePayload],
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        self._validate_chunk_size(chunk_size)
        if not payloads:
            LOGGER.debug("Async publish-batch skipped: empty payload list")
            return

        LOGGER.debug(
            "Async publish-batch start (payload_count=%s, chunk_size=%s, parse=%s)",
            len(payloads),
            chunk_size,
            parse,
        )
        servicebus_message: ASBMessageType = load_asb_message_type()
        async_client: ASBAsyncClient = await self._client_provider.create_async_client()
        async with async_client as client:
            async with self._entity_client.get_async_sender(client, self._publisher) as sender:
                messages: list[object] = self._build_servicebus_messages(
                    payloads,
                    servicebus_message=servicebus_message,
                    parse=parse,
                    parser=parser,
                )
                batches: list[object] = await self._asb_operations.build_async_batches(
                    sender,
                    messages,
                    chunk_size=chunk_size,
                )
                LOGGER.debug("Async publish-batch built batches=%s", len(batches))

                await asyncio.gather(*(sender.send_messages(batch) for batch in batches))

        LOGGER.debug("Async publish-batch completed (payload_count=%s)", len(payloads))


__all__ = ["AsyncPublisherStrategy"]
