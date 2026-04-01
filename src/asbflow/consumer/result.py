from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asbflow.exceptions import ConsumeError


@dataclass(frozen=True, slots=True)
class ConsumedPayloadFailure:
    """Failure details for one consumed message.

    Parameters
    ----------
    error : Exception
        Error raised while decoding, parsing, or settling the message.
    message_body : str | None, default=None
        Raw message body, when available.
    """

    error: Exception
    message_body: str | None = None


@dataclass(frozen=True, slots=True)
class RawConsumedMessage:
    """Successfully consumed raw message payload.

    Parameters
    ----------
    payload : dict[str, Any]
        Decoded JSON payload.
    message_body : str | None, default=None
        Original message body string.
    """

    payload: dict[str, Any]
    message_body: str | None = None


@dataclass(frozen=True, slots=True)
class RawConsumeResult:
    """Result of a raw consume operation.

    Parameters
    ----------
    raw_messages : list[RawConsumedMessage]
        Successfully consumed raw messages.
    errors : list[ConsumedPayloadFailure]
        Collected message-level failures.
    """

    raw_messages: list[RawConsumedMessage] = field(default_factory=list)
    errors: list[ConsumedPayloadFailure] = field(default_factory=list)

    @property
    def successes(self) -> list[dict[str, Any]]:
        return [m.payload for m in self.raw_messages]

    @property
    def failures(self) -> list[ConsumedPayloadFailure]:
        return self.errors

    @property
    def failed(self) -> bool:
        return len(self.errors) > 0

    @property
    def succeeded(self) -> bool:
        return not self.failed


@dataclass(frozen=True, slots=True)
class ParsedConsumeResult:
    """Result of a parsed consume operation.

    Parameters
    ----------
    parsed_messages : list[Any]
        Successfully parsed payload objects.
    errors : list[ConsumedPayloadFailure]
        Collected message-level failures.
    """

    parsed_messages: list[Any] = field(default_factory=list)
    errors: list[ConsumedPayloadFailure] = field(default_factory=list)

    @property
    def successes(self) -> list[Any]:
        return self.parsed_messages

    @property
    def failures(self) -> list[ConsumedPayloadFailure]:
        return self.errors

    @property
    def failed(self) -> bool:
        return len(self.errors) > 0

    @property
    def succeeded(self) -> bool:
        return not self.failed


ConsumeResult = ParsedConsumeResult | RawConsumeResult


__all__ = [
    "RawConsumedMessage",
    "RawConsumeResult",
    "ParsedConsumeResult",
    "ConsumeResult",
    "ConsumedPayloadFailure",
    "ConsumeError",
]
