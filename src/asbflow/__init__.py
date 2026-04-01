from importlib.metadata import PackageNotFoundError, version

from asbflow.config import (
    ASBAuthMethod,
    ASBConnectionConfig,
    ASBConsumerConfig,
    ASBMessageConfig,
    ASBMessagingEntity,
    ASBPublisherConfig,
    ParseFailurePolicy,
)
from asbflow.consumer import (
    ASBConsumer,
    ConsumedPayloadFailure,
    ConsumeExecutionMode,
    ConsumeResult,
    ParsedConsumeResult,
    PydanticModelParser,
    RawConsumeResult,
    create_consumer,
)
from asbflow.dlq import (
    ASBDLQManager,
    DLQParsedReadResult,
    DLQPurgeResult,
    DLQRawReadResult,
    DLQReadResult,
    DLQRedriveResult,
    create_dlq_manager,
)
from asbflow.exceptions import (
    ConsumeError,
    DLQError,
    DLQPublisherNotConfiguredError,
    PublishError,
)
from asbflow.publisher import ASBPublisher, PublishExecutionMode, create_publisher

try:
    __version__ = version("asbflow")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "ASBConnectionConfig",
    "ASBPublisherConfig",
    "ASBConsumerConfig",
    "ASBMessagingEntity",
    "ParseFailurePolicy",
    "ASBAuthMethod",
    "ASBMessageConfig",
    "ASBPublisher",
    "create_publisher",
    "PublishExecutionMode",
    "ASBConsumer",
    "create_consumer",
    "ASBDLQManager",
    "create_dlq_manager",
    "ConsumeExecutionMode",
    "RawConsumeResult",
    "ParsedConsumeResult",
    "ConsumeResult",
    "ConsumedPayloadFailure",
    "DLQRawReadResult",
    "DLQParsedReadResult",
    "DLQReadResult",
    "DLQRedriveResult",
    "DLQPurgeResult",
    "ConsumeError",
    "PublishError",
    "DLQError",
    "DLQPublisherNotConfiguredError",
    "PydanticModelParser",
]
