from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ASBAuthMethod(str, Enum):
    CONNECTION_STRING = "connection_string"
    MANAGED_IDENTITY = "managed_identity"

    @classmethod
    def parse(cls, value: "ASBAuthMethod | str") -> "ASBAuthMethod":
        if isinstance(value, cls):
            return value

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "connection_string": cls.CONNECTION_STRING,
            "conn_str": cls.CONNECTION_STRING,
            "managed_identity": cls.MANAGED_IDENTITY,
            "mi": cls.MANAGED_IDENTITY,
        }
        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unknown auth method: {value}. " "Supported values are connection_string and managed_identity."
            ) from exc


@dataclass(frozen=True, slots=True)
class ASBConnectionConfig:
    auth_method: ASBAuthMethod | str = ASBAuthMethod.CONNECTION_STRING
    connection_string: str | None = None
    fully_qualified_namespace: str | None = None
    managed_identity_client_id: str | None = None
    credential: Any | None = None
    logging_enable: bool = False
    transport_type: Any | None = None
    http_proxy: dict[str, Any] | None = None
    user_agent: str | None = None
    custom_endpoint_address: str | None = None
    client_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        resolved_auth_method: ASBAuthMethod = ASBAuthMethod.parse(self.auth_method)
        object.__setattr__(self, "auth_method", resolved_auth_method)
        object.__setattr__(self, "client_kwargs", dict(self.client_kwargs))

        if resolved_auth_method is ASBAuthMethod.CONNECTION_STRING and not self.connection_string:
            raise ValueError("connection_string is required when auth_method='connection_string'")

        if resolved_auth_method is ASBAuthMethod.MANAGED_IDENTITY and not self.fully_qualified_namespace:
            raise ValueError("fully_qualified_namespace is required when auth_method='managed_identity'")

    def _base_client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "logging_enable": self.logging_enable,
        }
        optional_map: dict[str, Any] = {
            "transport_type": self.transport_type,
            "http_proxy": self.http_proxy,
            "user_agent": self.user_agent,
            "custom_endpoint_address": self.custom_endpoint_address,
        }
        kwargs.update({k: v for k, v in optional_map.items() if v is not None})
        kwargs.update(self.client_kwargs)
        return kwargs

    @property
    def auth(self) -> ASBAuthMethod:
        value = self.auth_method
        if isinstance(value, ASBAuthMethod):
            return value
        return ASBAuthMethod.parse(value)

    def to_connection_string_client_kwargs(self) -> dict[str, Any]:
        if self.auth_method is not ASBAuthMethod.CONNECTION_STRING:
            raise ValueError("to_connection_string_client_kwargs can be used only with connection_string auth")

        kwargs = self._base_client_kwargs()
        kwargs["conn_str"] = self.connection_string
        return kwargs

    def to_managed_identity_client_kwargs(self, *, credential: Any) -> dict[str, Any]:
        if self.auth_method is not ASBAuthMethod.MANAGED_IDENTITY:
            raise ValueError("to_managed_identity_client_kwargs can be used only with managed_identity auth")

        kwargs = self._base_client_kwargs()
        kwargs["fully_qualified_namespace"] = self.fully_qualified_namespace
        kwargs["credential"] = credential
        return kwargs


__all__ = ["ASBConnectionConfig", "ASBAuthMethod"]
