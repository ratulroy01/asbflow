from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from overrides import override

from asbflow.config.defaults import (
    DEFAULT_PUBLISH_THREAD_POOL_MAX_WORKERS,
    get_asbflow_logger,
)
from asbflow.shared.parsing import PydanticModelParser
from asbflow.shared.sdk import load_asb_message_type

from ..base import BasePublisherStrategy, PublishablePayload

LOGGER = get_asbflow_logger(__name__)


class ThreadPoolPublisherStrategy(BasePublisherStrategy):
    @override
    def publish_batch(
        self,
        payloads: list[PublishablePayload],
        *,
        chunk_size: int | None = None,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> None:
        self._validate_chunk_size(chunk_size)
        if not payloads:
            LOGGER.debug("Thread-pool publish-batch skipped: empty payload list")
            return

        LOGGER.debug(
            "Thread-pool publish-batch start (payload_count=%s, chunk_size=%s, parse=%s)",
            len(payloads),
            chunk_size,
            parse,
        )
        servicebus_message = load_asb_message_type()
        with self._client_provider.create_sync_client() as client:
            with self._entity_client.get_sync_sender(client, self._publisher) as sender:
                messages: list[object] = self._build_servicebus_messages(
                    payloads,
                    servicebus_message=servicebus_message,
                    parse=parse,
                    parser=parser,
                )
                batches: list[object] = self._build_sync_batches(
                    sender,
                    messages,
                    chunk_size=chunk_size,
                )
                LOGGER.debug("Thread-pool publish-batch built batches=%s", len(batches))

                if len(batches) <= 1:
                    for batch in batches:
                        sender.send_messages(batch)
                    LOGGER.debug("Thread-pool publish-batch completed with single batch")
                    return

                with ThreadPoolExecutor(
                    max_workers=min(
                        len(batches),
                        DEFAULT_PUBLISH_THREAD_POOL_MAX_WORKERS,
                    )
                ) as executor:
                    list(executor.map(sender.send_messages, batches))

        LOGGER.debug("Thread-pool publish-batch completed (payload_count=%s)", len(payloads))


__all__ = ["ThreadPoolPublisherStrategy"]
