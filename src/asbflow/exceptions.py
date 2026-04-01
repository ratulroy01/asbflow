from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asbflow.consumer.result import ConsumeResult


class ConsumeError(Exception):
    """Raised when consume operations complete with one or more message-level failures."""

    def __init__(self, result: "ConsumeResult") -> None:
        super().__init__(f"Found {len(result.errors)} consume errors")
        self.result: "ConsumeResult" = result


class PublishError(Exception):
    """Raised when a publish operation fails."""

    def __init__(self, operation: str, error: Exception) -> None:
        super().__init__(f"Publish {operation} failed")
        self.operation: str = operation
        self.error: Exception = error


class DLQError(Exception):
    """Raised when a DLQ operation completes with one or more failures."""

    def __init__(self, operation: str, result: Any) -> None:
        super().__init__(f"DLQ {operation} completed with failures")
        self.operation: str = operation
        self.result: Any = result


class DLQPublisherNotConfiguredError(Exception):
    """Raised when DLQ redrive is requested without a configured publisher."""


__all__ = [
    "ConsumeError",
    "PublishError",
    "DLQError",
    "DLQPublisherNotConfiguredError",
]
