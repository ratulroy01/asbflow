from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Any


class ASBAuthMethod(str, Enum):
    CONNECTION_STRING = "connection_string"
    CLIENT_SECRET_CREDENTIAL = "client_secret_credential"
    MANAGED_IDENTITY = "managed_identity"
    DEFAULT_AZURE_CREDENTIAL = "default_azure_credential"

    @classmethod
    def parse(cls, value: "ASBAuthMethod | str") -> "ASBAuthMethod":
        if isinstance(value, cls):
            return value

        normalized: str = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases: dict[str, ASBAuthMethod] = {
            "connection_string": cls.CONNECTION_STRING,
            "connection_str": cls.CONNECTION_STRING,
            "conn_str": cls.CONNECTION_STRING,
            "client_secret_credential": cls.CLIENT_SECRET_CREDENTIAL,
            "client_secret": cls.CLIENT_SECRET_CREDENTIAL,
            "csc": cls.CLIENT_SECRET_CREDENTIAL,
            "managed_identity": cls.MANAGED_IDENTITY,
            "mi": cls.MANAGED_IDENTITY,
            "default_azure_credential": cls.DEFAULT_AZURE_CREDENTIAL,
            "default_az_credential": cls.DEFAULT_AZURE_CREDENTIAL,
            "def_azure_credential": cls.DEFAULT_AZURE_CREDENTIAL,
            "def_az_credential": cls.DEFAULT_AZURE_CREDENTIAL,
            "default_credential": cls.DEFAULT_AZURE_CREDENTIAL,
            "defaultazurecredential": cls.DEFAULT_AZURE_CREDENTIAL,
            "dac": cls.DEFAULT_AZURE_CREDENTIAL,
        }
        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unknown auth method: {value}. "
                "Supported values are connection_string, managed_identity, "
                "default_azure_credential and client_secret_credential."
            ) from exc


@dataclass(frozen=True, slots=True)
class ASBConnectionConfig:
    auth_method: ASBAuthMethod | str = ASBAuthMethod.CONNECTION_STRING
    connection_string: str | None = None
    fully_qualified_namespace: str | None = None
    client_id: str | None = None
    managed_identity_client_id: InitVar[str | None] = None
    client_secret_tenant_id: str | None = None
    client_secret_client_secret: str | None = None
    credential: Any | None = None
    logging_enable: bool = False
    transport_type: Any | None = None
    http_proxy: dict[str, Any] | None = None
    user_agent: str | None = None
    custom_endpoint_address: str | None = None
    client_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self, managed_identity_client_id: str | None) -> None:
        resolved_auth_method: ASBAuthMethod = ASBAuthMethod.parse(self.auth_method)
        object.__setattr__(self, "auth_method", resolved_auth_method)
        object.__setattr__(self, "client_kwargs", dict(self.client_kwargs))
        if self.client_id is None and managed_identity_client_id is not None:
            object.__setattr__(self, "client_id", managed_identity_client_id)

        if resolved_auth_method is ASBAuthMethod.CONNECTION_STRING and not self.connection_string:
            raise ValueError("connection_string is required when auth_method='connection_string'")

        if (
            resolved_auth_method
            in (
                ASBAuthMethod.MANAGED_IDENTITY,
                ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL,
                ASBAuthMethod.CLIENT_SECRET_CREDENTIAL,
            )
            and not self.fully_qualified_namespace
        ):
            raise ValueError(
                "fully_qualified_namespace is required when auth_method is "
                "'managed_identity', 'default_azure_credential' "
                "or 'client_secret_credential'"
            )

        if (
            resolved_auth_method is ASBAuthMethod.CLIENT_SECRET_CREDENTIAL
            and self.credential is None
            and not (self.client_secret_tenant_id and self.client_id and self.client_secret_client_secret)
        ):
            raise ValueError(
                "client_secret_tenant_id, client_id and "
                "client_secret_client_secret are required when "
                "auth_method='client_secret_credential' and no explicit "
                "credential is provided"
            )

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

        kwargs: dict[str, Any] = self._base_client_kwargs()
        kwargs["conn_str"] = self.connection_string
        return kwargs

    def to_token_credential_client_kwargs(self, *, credential: Any) -> dict[str, Any]:
        if self.auth_method not in (
            ASBAuthMethod.MANAGED_IDENTITY,
            ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL,
            ASBAuthMethod.CLIENT_SECRET_CREDENTIAL,
        ):
            raise ValueError(
                "to_token_credential_client_kwargs can be used only with "
                "managed_identity, default_azure_credential or "
                "client_secret_credential auth"
            )

        kwargs: dict[str, Any] = self._base_client_kwargs()
        kwargs["fully_qualified_namespace"] = self.fully_qualified_namespace
        kwargs["credential"] = credential
        return kwargs

    def to_managed_identity_client_kwargs(self, *, credential: Any) -> dict[str, Any]:
        return self.to_token_credential_client_kwargs(credential=credential)

    def to_client_secret_credential_kwargs(self) -> dict[str, Any]:
        if self.auth_method is not ASBAuthMethod.CLIENT_SECRET_CREDENTIAL:
            raise ValueError(
                "to_client_secret_credential_kwargs can be used only with " "client_secret_credential auth"
            )

        return {
            "tenant_id": self.client_secret_tenant_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret_client_secret,
        }


__all__ = ["ASBConnectionConfig", "ASBAuthMethod"]
