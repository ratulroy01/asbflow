from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

from asbflow.auth.base import ASBClientProvider
from asbflow.config.connection import ASBConnectionConfig
from asbflow.config.defaults import get_asbflow_logger
from asbflow.shared.sdk import (
    ASBAsyncClient,
    ASBAsyncClientFactory,
    ASBSyncClient,
    ASBSyncClientFactory,
    load_asb_async_client,
    load_asb_client_factory,
)

LOGGER = get_asbflow_logger(__name__)


class ConnectionStringClientProvider(ASBClientProvider):
    """Create clients using Service Bus connection-string authentication."""

    def create_sync_client(self) -> ASBSyncClient:
        """Create a synchronous client from connection-string auth.

        Returns
        -------
        ASBSyncClient
            Synchronous Service Bus client.
        """
        LOGGER.info("Creating synchronous ASB client with connection-string auth")
        servicebus_client: ASBSyncClientFactory = load_asb_client_factory()
        LOGGER.debug(
            "Loaded sync ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client.from_connection_string(**self.config.to_connection_string_client_kwargs())

    async def create_async_client(self) -> ASBAsyncClient:
        """Create an asynchronous client from connection-string auth.

        Returns
        -------
        ASBAsyncClient
            Asynchronous Service Bus client.
        """
        LOGGER.info("Creating asynchronous ASB client with connection-string auth")
        servicebus_client: ASBAsyncClientFactory = load_asb_async_client()
        LOGGER.debug(
            "Loaded async ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client.from_connection_string(**self.config.to_connection_string_client_kwargs())


class ClientSecretCredentialClientProvider(ASBClientProvider):
    """Create clients using Azure ClientSecretCredential authentication."""

    def _build_credential(self) -> Any:
        config: ASBConnectionConfig = self.config
        if config.credential is not None:
            LOGGER.debug("Using explicit credential instance from configuration")
            return self.config.credential

        try:
            identity_module: ModuleType = import_module("azure.identity")
        except Exception:
            LOGGER.exception("Unable to import azure.identity while building client-secret credential")
            raise

        credential_class: Any = getattr(identity_module, "ClientSecretCredential")
        LOGGER.debug("Building ClientSecretCredential from configuration")
        return credential_class(**config.to_client_secret_credential_kwargs())

    def _build_kwargs(self) -> dict[str, Any]:
        credential: Any = self._build_credential()
        LOGGER.debug(
            "Client-secret credential kwargs prepared (namespace=%s, logging_enable=%s)",
            self.config.fully_qualified_namespace,
            self.config.logging_enable,
        )
        return self.config.to_token_credential_client_kwargs(credential=credential)

    def create_sync_client(self) -> ASBSyncClient:
        """Create a synchronous client from client-secret credential auth.

        Returns
        -------
        ASBSyncClient
            Synchronous Service Bus client.
        """
        LOGGER.info("Creating synchronous ASB client with client-secret auth")
        servicebus_client: ASBSyncClientFactory = load_asb_client_factory()
        LOGGER.debug(
            "Loaded sync ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client(**self._build_kwargs())

    async def create_async_client(self) -> ASBAsyncClient:
        """Create an asynchronous client from client-secret credential auth.

        Returns
        -------
        ASBAsyncClient
            Asynchronous Service Bus client.
        """
        LOGGER.info("Creating asynchronous ASB client with client-secret auth")
        servicebus_client: ASBAsyncClientFactory = load_asb_async_client()
        LOGGER.debug(
            "Loaded async ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client(**self._build_kwargs())


class ManagedIdentityClientProvider(ASBClientProvider):
    """Create clients using Azure Managed Identity authentication."""

    def _build_credential(self) -> Any:
        config: ASBConnectionConfig = self.config
        if config.credential is not None:
            LOGGER.debug("Using explicit credential instance from configuration")
            return self.config.credential

        try:
            identity_module: ModuleType = import_module("azure.identity")
        except Exception:
            LOGGER.exception("Unable to import azure.identity while building managed-identity credential")
            raise

        credential_class: Any = getattr(identity_module, "ManagedIdentityCredential")
        if config.client_id is not None:
            LOGGER.debug("Building ManagedIdentityCredential with client_id")
            return credential_class(client_id=config.client_id)

        LOGGER.debug("Building default ManagedIdentityCredential")
        return credential_class()

    def _build_kwargs(self) -> dict[str, Any]:
        credential: Any = self._build_credential()
        LOGGER.debug(
            "Managed-identity client kwargs prepared (namespace=%s, logging_enable=%s)",
            self.config.fully_qualified_namespace,
            self.config.logging_enable,
        )
        return self.config.to_token_credential_client_kwargs(credential=credential)

    def create_sync_client(self) -> ASBSyncClient:
        """Create a synchronous client from managed-identity auth.

        Returns
        -------
        ASBSyncClient
            Synchronous Service Bus client.
        """
        LOGGER.info("Creating synchronous ASB client with managed-identity auth")
        servicebus_client: ASBSyncClientFactory = load_asb_client_factory()
        LOGGER.debug(
            "Loaded sync ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client(**self._build_kwargs())

    async def create_async_client(self) -> ASBAsyncClient:
        """Create an asynchronous client from managed-identity auth.

        Returns
        -------
        ASBAsyncClient
            Asynchronous Service Bus client.
        """
        LOGGER.info("Creating asynchronous ASB client with managed-identity auth")
        servicebus_client: ASBAsyncClientFactory = load_asb_async_client()
        LOGGER.debug(
            "Loaded async ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client(**self._build_kwargs())


class DefaultAzureCredentialClientProvider(ASBClientProvider):
    """Create clients using Azure DefaultAzureCredential authentication."""

    def _build_credential(self) -> Any:
        config: ASBConnectionConfig = self.config
        if config.credential is not None:
            LOGGER.debug("Using explicit credential instance from configuration")
            return self.config.credential

        try:
            identity_module: ModuleType = import_module("azure.identity")
        except Exception:
            LOGGER.exception("Unable to import azure.identity while building default-credential auth")
            raise

        credential_class: Any = getattr(identity_module, "DefaultAzureCredential")
        if config.client_id is not None:
            LOGGER.debug("Building DefaultAzureCredential with client_id")
            return credential_class(managed_identity_client_id=config.client_id)

        LOGGER.debug("Building default DefaultAzureCredential")
        return credential_class()

    def _build_kwargs(self) -> dict[str, Any]:
        credential: Any = self._build_credential()
        LOGGER.debug(
            "Default-credential client kwargs prepared (namespace=%s, logging_enable=%s)",
            self.config.fully_qualified_namespace,
            self.config.logging_enable,
        )
        return self.config.to_token_credential_client_kwargs(credential=credential)

    def create_sync_client(self) -> ASBSyncClient:
        """Create a synchronous client from DefaultAzureCredential auth.

        Returns
        -------
        ASBSyncClient
            Synchronous Service Bus client.
        """
        LOGGER.info("Creating synchronous ASB client with default-credential auth")
        servicebus_client: ASBSyncClientFactory = load_asb_client_factory()
        LOGGER.debug(
            "Loaded sync ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client(**self._build_kwargs())

    async def create_async_client(self) -> ASBAsyncClient:
        """Create an asynchronous client from DefaultAzureCredential auth.

        Returns
        -------
        ASBAsyncClient
            Asynchronous Service Bus client.
        """
        LOGGER.info("Creating asynchronous ASB client with default-credential auth")
        servicebus_client: ASBAsyncClientFactory = load_asb_async_client()
        LOGGER.debug(
            "Loaded async ASB factory class: %s",
            type(servicebus_client).__name__,
        )
        return servicebus_client(**self._build_kwargs())


__all__ = [
    "ConnectionStringClientProvider",
    "ManagedIdentityClientProvider",
    "DefaultAzureCredentialClientProvider",
    "ClientSecretCredentialClientProvider",
]
