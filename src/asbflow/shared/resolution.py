from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class PropertyResolver(Generic[T]):
    """Resolve an optional override against a default value."""

    def __init__(self, default: T) -> None:
        self._default: T = default

    @property
    def default(self) -> T:
        return self._default

    def resolve(self, override: T | None = None) -> T:
        return self._default if override is None else override


__all__ = ["PropertyResolver"]
