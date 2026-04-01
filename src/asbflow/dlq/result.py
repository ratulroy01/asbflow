from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class DLQRawReadResult:
    """Result of a raw DLQ read operation.

    Parameters
    ----------
    messages : list[dict[str, object]]
        Successfully read raw payloads.
    failed_payloads : list[str]
        Payload bodies that failed processing.
    """

    messages: list[dict[str, object]] = field(default_factory=list)
    failed_payloads: list[str] = field(default_factory=list)

    @property
    def successes(self) -> list[dict[str, object]]:
        return self.messages

    @property
    def failures(self) -> list[str]:
        return self.failed_payloads

    @property
    def succeeded(self) -> bool:
        return len(self.failed_payloads) == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded


@dataclass(frozen=True, slots=True)
class DLQParsedReadResult:
    """Result of a parsed DLQ read operation.

    Parameters
    ----------
    parsed : list[BaseModel]
        Successfully parsed payloads.
    failed_payloads : list[str]
        Payload bodies that failed processing.
    """

    parsed: list[BaseModel] = field(default_factory=list)
    failed_payloads: list[str] = field(default_factory=list)

    @property
    def successes(self) -> list[BaseModel]:
        return self.parsed

    @property
    def failures(self) -> list[str]:
        return self.failed_payloads

    @property
    def succeeded(self) -> bool:
        return len(self.failed_payloads) == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded


DLQReadResult = DLQParsedReadResult | DLQRawReadResult


@dataclass(frozen=True, slots=True)
class DLQRedriveResult:
    """Result of a DLQ redrive operation.

    Parameters
    ----------
    republished : int
        Number of messages republished successfully.
    parse_failed : int
        Number of messages failed during parsing.
    publish_failed : int
        Number of messages failed during republish.
    """

    republished: int
    parse_failed: int
    publish_failed: int

    @property
    def succeeded(self) -> bool:
        return self.parse_failed == 0 and self.publish_failed == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded


@dataclass(frozen=True, slots=True)
class DLQPurgeResult:
    """Result of a DLQ purge operation.

    Parameters
    ----------
    purged : int
        Number of purged messages.
    errors : int
        Number of purge errors.
    """

    purged: int
    errors: int

    @property
    def succeeded(self) -> bool:
        return self.errors == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded


__all__ = [
    "DLQRawReadResult",
    "DLQParsedReadResult",
    "DLQReadResult",
    "DLQRedriveResult",
    "DLQPurgeResult",
]
