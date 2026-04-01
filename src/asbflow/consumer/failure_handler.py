from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from asbflow.config import ParseFailurePolicy
from asbflow.config.defaults import get_asbflow_logger
from asbflow.consumer.result import ConsumedPayloadFailure
from asbflow.shared.message import decode_message_body

LOGGER = get_asbflow_logger(__name__)


class ConsumeFailureHandler:
    @staticmethod
    def is_transient_error(error: Exception) -> bool:
        retryable = getattr(error, "retryable", None)
        if isinstance(retryable, bool):
            return retryable

        transient = getattr(error, "is_transient", None)
        if isinstance(transient, bool):
            return transient

        if isinstance(
            error,
            (
                ValidationError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
                NotImplementedError,
                AssertionError,
                UnicodeDecodeError,
            ),
        ):
            return False

        error_name = type(error).__name__.lower()
        if any(
            token in error_name
            for token in (
                "validation",
                "schema",
                "decode",
                "encode",
                "deserialize",
                "serialize",
                "valueerror",
                "typeerror",
                "keyerror",
                "attributeerror",
                "notimplemented",
                "assertion",
            )
        ):
            return False

        return True

    def settle_failed_message(
        self,
        receiver: Any,
        raw_message: Any,
        policy: ParseFailurePolicy,
    ) -> None:
        try:
            if policy is ParseFailurePolicy.LEAVE_UNSETTLED:
                return
            if policy is ParseFailurePolicy.COMPLETE:
                receiver.complete_message(raw_message)
                return
            if policy is ParseFailurePolicy.ABANDON:
                receiver.abandon_message(raw_message)
                return
            receiver.dead_letter_message(raw_message)
        except Exception:
            LOGGER.exception(
                "Failed to settle malformed message",
                extra={"policy": policy.value},
            )
            raise

    async def asettle_failed_message(
        self,
        receiver: Any,
        raw_message: Any,
        policy: ParseFailurePolicy,
    ) -> None:
        try:
            if policy is ParseFailurePolicy.LEAVE_UNSETTLED:
                return
            if policy is ParseFailurePolicy.COMPLETE:
                await receiver.complete_message(raw_message)
                return
            if policy is ParseFailurePolicy.ABANDON:
                await receiver.abandon_message(raw_message)
                return
            await receiver.dead_letter_message(raw_message)
        except Exception:
            LOGGER.exception(
                "Failed to settle malformed message (async)",
                extra={"policy": policy.value},
            )
            raise

    def handle_transient_consume_error(
        self,
        receiver: Any,
        raw_message: Any,
        error: Exception,
        errors: list[ConsumedPayloadFailure],
    ) -> None:
        if not self.is_transient_error(error):
            LOGGER.exception("Non-transient consume error encountered")
            raise error

        LOGGER.exception("Transient consume error encountered; abandoning message")
        receiver.abandon_message(raw_message)

        message_body: str | None = None
        try:
            message_body = decode_message_body(raw_message)
        except (UnicodeDecodeError, ValueError, TypeError):
            pass

        errors.append(ConsumedPayloadFailure(error=error, message_body=message_body))

    async def ahandle_transient_consume_error(
        self,
        receiver: Any,
        raw_message: Any,
        error: Exception,
        errors: list[ConsumedPayloadFailure],
    ) -> None:
        if not self.is_transient_error(error):
            LOGGER.exception("Non-transient consume error encountered (async)")
            raise error

        LOGGER.exception("Transient consume error encountered (async); abandoning message")
        await receiver.abandon_message(raw_message)

        message_body: str | None = None
        try:
            message_body = decode_message_body(raw_message)
        except (UnicodeDecodeError, ValueError, TypeError):
            pass

        errors.append(ConsumedPayloadFailure(error=error, message_body=message_body))


__all__ = ["ConsumeFailureHandler"]
