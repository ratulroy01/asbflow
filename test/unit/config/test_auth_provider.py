from __future__ import annotations

import asyncio

from asbflow.auth import (
    ASBClientProviderFactory,
    ClientSecretCredentialClientProvider,
    ConnectionStringClientProvider,
    DefaultAzureCredentialClientProvider,
    ManagedIdentityClientProvider,
)
from asbflow.config import ASBAuthMethod, ASBConnectionConfig


class _FakeSyncClientFactory:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def from_connection_string(self, **kwargs: object) -> object:
        self.kwargs = dict(kwargs)
        return object()


class _FakeDirectClientFactory:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def __call__(self, **kwargs: object) -> object:
        self.kwargs = dict(kwargs)
        return object()


def test_connection_string_provider_uses_from_connection_string(monkeypatch):
    cfg = ASBConnectionConfig(connection_string="Endpoint=sb://test/", logging_enable=True)
    provider = ConnectionStringClientProvider(cfg)
    factory = _FakeSyncClientFactory()
    monkeypatch.setattr("asbflow.auth.providers.load_asb_client_factory", lambda: factory)
    monkeypatch.setattr("asbflow.auth.providers.load_asb_async_client", lambda: factory)

    _ = provider.create_sync_client()
    _ = asyncio.run(provider.create_async_client())

    assert factory.kwargs is not None
    assert factory.kwargs["conn_str"] == "Endpoint=sb://test/"
    assert factory.kwargs["logging_enable"] is True


def test_managed_identity_provider_uses_direct_constructor(monkeypatch):
    credential = object()
    cfg = ASBConnectionConfig(
        auth_method=ASBAuthMethod.MANAGED_IDENTITY,
        fully_qualified_namespace="ns.servicebus.windows.net",
        credential=credential,
    )
    provider = ManagedIdentityClientProvider(cfg)
    factory = _FakeDirectClientFactory()
    monkeypatch.setattr("asbflow.auth.providers.load_asb_client_factory", lambda: factory)
    monkeypatch.setattr("asbflow.auth.providers.load_asb_async_client", lambda: factory)

    _ = provider.create_sync_client()
    _ = asyncio.run(provider.create_async_client())

    assert factory.kwargs is not None
    assert factory.kwargs["fully_qualified_namespace"] == "ns.servicebus.windows.net"
    assert factory.kwargs["credential"] is credential


def test_auth_provider_factory_connection_string_default():
    cfg = ASBConnectionConfig(connection_string="Endpoint=sb://test/")
    provider = ASBClientProviderFactory.create(cfg)
    assert isinstance(provider, ConnectionStringClientProvider)


def test_auth_provider_factory_managed_identity():
    cfg = ASBConnectionConfig(
        auth_method=ASBAuthMethod.MANAGED_IDENTITY,
        fully_qualified_namespace="ns.servicebus.windows.net",
        credential=object(),
    )
    provider = ASBClientProviderFactory.create(cfg)
    assert isinstance(provider, ManagedIdentityClientProvider)


def test_default_azure_credential_provider_uses_direct_constructor(monkeypatch):
    credential = object()
    cfg = ASBConnectionConfig(
        auth_method=ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL,
        fully_qualified_namespace="ns.servicebus.windows.net",
        credential=credential,
    )
    provider = DefaultAzureCredentialClientProvider(cfg)
    factory = _FakeDirectClientFactory()
    monkeypatch.setattr("asbflow.auth.providers.load_asb_client_factory", lambda: factory)
    monkeypatch.setattr("asbflow.auth.providers.load_asb_async_client", lambda: factory)

    _ = provider.create_sync_client()
    _ = asyncio.run(provider.create_async_client())

    assert factory.kwargs is not None
    assert factory.kwargs["fully_qualified_namespace"] == "ns.servicebus.windows.net"
    assert factory.kwargs["credential"] is credential


def test_client_secret_credential_provider_uses_direct_constructor(monkeypatch):
    credential = object()
    cfg = ASBConnectionConfig(
        auth_method=ASBAuthMethod.CLIENT_SECRET_CREDENTIAL,
        fully_qualified_namespace="ns.servicebus.windows.net",
        credential=credential,
    )
    provider = ClientSecretCredentialClientProvider(cfg)
    factory = _FakeDirectClientFactory()
    monkeypatch.setattr("asbflow.auth.providers.load_asb_client_factory", lambda: factory)
    monkeypatch.setattr("asbflow.auth.providers.load_asb_async_client", lambda: factory)

    _ = provider.create_sync_client()
    _ = asyncio.run(provider.create_async_client())

    assert factory.kwargs is not None
    assert factory.kwargs["fully_qualified_namespace"] == "ns.servicebus.windows.net"
    assert factory.kwargs["credential"] is credential


def test_auth_provider_factory_default_azure_credential():
    cfg = ASBConnectionConfig(
        auth_method=ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL,
        fully_qualified_namespace="ns.servicebus.windows.net",
        credential=object(),
    )
    provider = ASBClientProviderFactory.create(cfg)
    assert isinstance(provider, DefaultAzureCredentialClientProvider)


def test_auth_provider_factory_client_secret_credential():
    cfg = ASBConnectionConfig(
        auth_method=ASBAuthMethod.CLIENT_SECRET_CREDENTIAL,
        fully_qualified_namespace="ns.servicebus.windows.net",
        credential=object(),
    )
    provider = ASBClientProviderFactory.create(cfg)
    assert isinstance(provider, ClientSecretCredentialClientProvider)
