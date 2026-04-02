from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from asbflow.shared.parsing import DecodedJsonMessage, decode_json_message
from asbflow.shared.payloads import PublishablePayload


class ServiceBusPayloadOperations:
    @staticmethod
    def validate_chunk_size(chunk_size: int | None) -> None:
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")

    @staticmethod
    def payload_to_json(payload: PublishablePayload) -> str:
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        return json.dumps(payload)

    def build_messages(
        self,
        payloads: list[PublishablePayload],
        *,
        servicebus_message: Any,
        message_kwargs: dict[str, Any],
    ) -> list[object]:
        return [servicebus_message(self.payload_to_json(payload), **message_kwargs) for payload in payloads]

    @staticmethod
    def decode_message(raw_message: Any) -> DecodedJsonMessage:
        return decode_json_message(raw_message)

    def build_sync_batches(
        self,
        sender: Any,
        messages: list[object],
        *,
        chunk_size: int | None = None,
    ) -> list[object]:
        if not messages:
            return []

        batches: list[object] = []
        current_batch: Any = sender.create_message_batch()
        current_count: int = 0

        for message in messages:
            if chunk_size is not None and current_count >= chunk_size:
                batches.append(current_batch)
                current_batch = sender.create_message_batch()
                current_count = 0

            try:
                current_batch.add_message(message)
            except ValueError as exc:
                if len(current_batch) == 0:
                    raise ValueError("A single message exceeds the batch size limit") from exc

                batches.append(current_batch)
                current_batch = sender.create_message_batch()
                current_count = 0
                current_batch.add_message(message)

            current_count += 1

        batches.append(current_batch)
        return batches

    async def build_async_batches(
        self,
        sender: Any,
        messages: list[object],
        *,
        chunk_size: int | None = None,
    ) -> list[object]:
        if not messages:
            return []

        batches: list[object] = []
        current_batch: Any = await sender.create_message_batch()
        current_count: int = 0

        for message in messages:
            if chunk_size is not None and current_count >= chunk_size:
                batches.append(current_batch)
                current_batch = await sender.create_message_batch()
                current_count = 0

            try:
                current_batch.add_message(message)
            except ValueError as exc:
                if len(current_batch) == 0:
                    raise ValueError("A single message exceeds the batch size limit") from exc

                batches.append(current_batch)
                current_batch = await sender.create_message_batch()
                current_count = 0
                current_batch.add_message(message)

            current_count += 1

        batches.append(current_batch)
        return batches


__all__ = [
    "ServiceBusPayloadOperations",
]
