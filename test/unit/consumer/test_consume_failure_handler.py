import asyncio

import pytest

from asbflow.config import ParseFailurePolicy
from asbflow.consumer.failure_handler import ConsumeFailureHandler
from asbflow.consumer.result import ConsumedPayloadFailure


class _Message:
    def __init__(self, body):
        self.body = body


class _Receiver:
    def __init__(self) -> None:
        self.completed = []
        self.abandoned = []
        self.dead_lettered = []

    def complete_message(self, msg):
        self.completed.append(msg)

    def abandon_message(self, msg):
        self.abandoned.append(msg)

    def dead_letter_message(self, msg):
        self.dead_lettered.append(msg)


class _AsyncReceiver(_Receiver):
    async def complete_message(self, msg):
        self.completed.append(msg)

    async def abandon_message(self, msg):
        self.abandoned.append(msg)

    async def dead_letter_message(self, msg):
        self.dead_lettered.append(msg)


class _RetryableError(RuntimeError):
    retryable = True


def test_settle_failed_message_applies_policy() -> None:
    handler = ConsumeFailureHandler()
    receiver = _Receiver()
    message = _Message(b"{}")

    handler.settle_failed_message(receiver, message, ParseFailurePolicy.COMPLETE)
    handler.settle_failed_message(receiver, message, ParseFailurePolicy.ABANDON)
    handler.settle_failed_message(receiver, message, ParseFailurePolicy.DEAD_LETTER)
    handler.settle_failed_message(receiver, message, ParseFailurePolicy.LEAVE_UNSETTLED)

    assert len(receiver.completed) == 1
    assert len(receiver.abandoned) == 1
    assert len(receiver.dead_lettered) == 1


def test_handle_transient_consume_error_appends_failure() -> None:
    handler = ConsumeFailureHandler()
    receiver = _Receiver()
    message = _Message(b'{"id":"x"}')
    errors: list[ConsumedPayloadFailure] = []

    handler.handle_transient_consume_error(
        receiver,
        message,
        _RetryableError("temporary"),
        errors,
    )

    assert len(receiver.abandoned) == 1
    assert len(errors) == 1
    assert errors[0].message_body == '{"id":"x"}'


def test_handle_transient_consume_error_raises_non_transient() -> None:
    handler = ConsumeFailureHandler()
    receiver = _Receiver()
    message = _Message(b'{"id":"x"}')

    with pytest.raises(ValueError, match="bad"):
        handler.handle_transient_consume_error(
            receiver,
            message,
            ValueError("bad"),
            [],
        )


def test_asettle_failed_message_applies_policy() -> None:
    handler = ConsumeFailureHandler()
    receiver = _AsyncReceiver()
    message = _Message(b"{}")

    async def _run() -> None:
        await handler.asettle_failed_message(receiver, message, ParseFailurePolicy.DEAD_LETTER)

    asyncio.run(_run())
    assert len(receiver.dead_lettered) == 1


def test_ahandle_transient_consume_error_appends_failure() -> None:
    handler = ConsumeFailureHandler()
    receiver = _AsyncReceiver()
    message = _Message(b'{"id":"x"}')
    errors: list[ConsumedPayloadFailure] = []

    async def _run() -> None:
        await handler.ahandle_transient_consume_error(
            receiver,
            message,
            _RetryableError("temporary"),
            errors,
        )

    asyncio.run(_run())
    assert len(receiver.abandoned) == 1
    assert len(errors) == 1
