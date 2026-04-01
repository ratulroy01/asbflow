from __future__ import annotations

from importlib import import_module
from types import ModuleType, TracebackType
from typing import Any, Protocol, TypeAlias

from asbflow.config.defaults import DEFAULT_ASB_SDK_IMPORT_MODE, ASBSDKImportMode

# --------------------------------------------------------
# ASB client protocols
# --------------------------------------------------------


class ASBSyncClient(Protocol):
    def __enter__(self) -> "ASBSyncClient": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...

    def get_topic_sender(self, **kwargs: Any) -> Any: ...

    def get_queue_sender(self, **kwargs: Any) -> Any: ...

    def get_subscription_receiver(self, **kwargs: Any) -> Any: ...

    def get_queue_receiver(self, **kwargs: Any) -> Any: ...


class ASBAsyncClient(Protocol):
    async def __aenter__(self) -> "ASBAsyncClient": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...

    def get_topic_sender(self, **kwargs: Any) -> Any: ...

    def get_queue_sender(self, **kwargs: Any) -> Any: ...

    def get_subscription_receiver(self, **kwargs: Any) -> Any: ...

    def get_queue_receiver(self, **kwargs: Any) -> Any: ...


# --------------------------------------------------------
# ASB client factory protocols
# --------------------------------------------------------


class _ASBSyncClientFactoryProtocol(Protocol):
    @staticmethod
    def from_connection_string(**kwargs: Any) -> ASBSyncClient: ...

    def __call__(self, **kwargs: Any) -> ASBSyncClient: ...


class _ASBAsyncClientFactoryProtocol(Protocol):
    @staticmethod
    def from_connection_string(**kwargs: Any) -> ASBAsyncClient: ...

    def __call__(self, **kwargs: Any) -> ASBAsyncClient: ...


class _ASBMessageProtocol(Protocol):
    def __call__(self, body: str, **kwargs: Any) -> Any: ...


ASBSyncClientFactory: TypeAlias = _ASBSyncClientFactoryProtocol
ASBAsyncClientFactory: TypeAlias = _ASBAsyncClientFactoryProtocol
ASBMessageType: TypeAlias = _ASBMessageProtocol


# --------------------------------------------------------
# ASB library imports
# --------------------------------------------------------

_ASB_SYNC_MODULE: ModuleType | None = None
_ASB_ASYNC_MODULE: ModuleType | None = None


def _load_azure_servicebus_module(
    *,
    import_mode: ASBSDKImportMode = DEFAULT_ASB_SDK_IMPORT_MODE,
) -> ModuleType:
    global _ASB_SYNC_MODULE
    if import_mode is ASBSDKImportMode.LAZY:
        return import_module("azure.servicebus")

    if _ASB_SYNC_MODULE is None:
        _ASB_SYNC_MODULE = import_module("azure.servicebus")
    return _ASB_SYNC_MODULE


def _load_azure_servicebus_async_module(
    *,
    import_mode: ASBSDKImportMode = DEFAULT_ASB_SDK_IMPORT_MODE,
) -> ModuleType:
    global _ASB_ASYNC_MODULE
    if import_mode is ASBSDKImportMode.LAZY:
        return import_module("azure.servicebus.aio")

    if _ASB_ASYNC_MODULE is None:
        _ASB_ASYNC_MODULE = import_module("azure.servicebus.aio")
    return _ASB_ASYNC_MODULE


def load_asb_client_factory(
    *,
    import_mode: ASBSDKImportMode = DEFAULT_ASB_SDK_IMPORT_MODE,
) -> ASBSyncClientFactory:
    servicebus_module: ModuleType = _load_azure_servicebus_module(import_mode=import_mode)
    return servicebus_module.ServiceBusClient


def load_asb_async_client(
    *,
    import_mode: ASBSDKImportMode = DEFAULT_ASB_SDK_IMPORT_MODE,
) -> ASBAsyncClientFactory:
    servicebus_aio_module: ModuleType = _load_azure_servicebus_async_module(import_mode=import_mode)
    return servicebus_aio_module.ServiceBusClient


def load_asb_message_type(
    *,
    import_mode: ASBSDKImportMode = DEFAULT_ASB_SDK_IMPORT_MODE,
) -> ASBMessageType:
    servicebus_module: ModuleType = _load_azure_servicebus_module(import_mode=import_mode)
    return servicebus_module.ServiceBusMessage


def load_asb_dead_letter_subqueue(
    *,
    import_mode: ASBSDKImportMode = DEFAULT_ASB_SDK_IMPORT_MODE,
) -> object:
    servicebus_module: ModuleType = _load_azure_servicebus_module(import_mode=import_mode)
    sub_queue = getattr(servicebus_module, "ServiceBusSubQueue")
    return sub_queue.DEAD_LETTER


def preload_asb_modules() -> None:
    """Eagerly load Azure Service Bus sync and async modules."""
    _load_azure_servicebus_module(import_mode=ASBSDKImportMode.EAGER)
    _load_azure_servicebus_async_module(import_mode=ASBSDKImportMode.EAGER)


if DEFAULT_ASB_SDK_IMPORT_MODE is ASBSDKImportMode.EAGER:
    preload_asb_modules()


__all__ = [
    "ASBSyncClient",
    "ASBAsyncClient",
    "ASBSyncClientFactory",
    "ASBAsyncClientFactory",
    "ASBMessageType",
    "load_asb_client_factory",
    "load_asb_async_client",
    "load_asb_message_type",
    "load_asb_dead_letter_subqueue",
    "preload_asb_modules",
]
