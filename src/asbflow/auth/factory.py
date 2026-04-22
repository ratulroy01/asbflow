from __future__ import annotations

from asbflow.auth.base import ASBClientProvider
from asbflow.auth.providers import (
    ClientSecretCredentialClientProvider,
    ConnectionStringClientProvider,
    DefaultAzureCredentialClientProvider,
    ManagedIdentityClientProvider,
)
from asbflow.config.connection import ASBAuthMethod, ASBConnectionConfig


class ASBClientProviderFactory:
    """Build the client provider matching the configured auth method."""

    @staticmethod
    def create(config: ASBConnectionConfig) -> ASBClientProvider:
        """Create an auth provider.

        Parameters
        ----------
        config : ASBConnectionConfig
            Connection/auth configuration.

        Returns
        -------
        ASBClientProvider
            Provider implementation compatible with the selected auth method.

        Raises
        ------
        ValueError
            If the auth method is unsupported.
        """
        match config.auth:
            case ASBAuthMethod.CONNECTION_STRING:
                return ConnectionStringClientProvider(config)
            case ASBAuthMethod.CLIENT_SECRET_CREDENTIAL:
                return ClientSecretCredentialClientProvider(config)
            case ASBAuthMethod.MANAGED_IDENTITY:
                return ManagedIdentityClientProvider(config)
            case ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL:
                return DefaultAzureCredentialClientProvider(config)

        raise ValueError(f"Unsupported Service Bus auth method: {config.auth}")


__all__ = ["ASBClientProviderFactory"]
