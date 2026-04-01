from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Final


class ASBSDKImportMode(str, Enum):
    # Import Azure SDK modules on first usage.
    LAZY = "lazy"
    # Import Azure SDK modules at asbflow SDK initialization time.
    EAGER = "eager"


# ----------------------------------------------------
# Constants
# ----------------------------------------------------

# Default number of messages consumed per batch in generic consumers.
DEFAULT_MAX_MESSAGE_COUNT: Final[int] = 10
# Default number of DLQ messages read in a single management operation.
DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT: Final[int] = 50
# Default upper bound of DLQ messages purged in one call.
DEFAULT_DLQ_PURGE_MAX_MESSAGE_COUNT: Final[int] = 200
# Default publisher chunk size. `None` means SDK-driven batching only.
DEFAULT_CHUNK_SIZE: Final[int | None] = None
# Max worker threads for publisher thread-pool strategy.
DEFAULT_PUBLISH_THREAD_POOL_MAX_WORKERS: Final[int] = 8
# Max worker threads for consumer thread-pool strategy.
DEFAULT_CONSUME_THREAD_POOL_MAX_WORKERS: Final[int] = 32
# Default Azure SDK import mode used by shared SDK loaders.
DEFAULT_ASB_SDK_IMPORT_MODE: Final[ASBSDKImportMode] = ASBSDKImportMode.LAZY

# ----------------------------------------------------
# Logger
# ----------------------------------------------------

# Base logger name for all asbflow logs.
ASBFLOW_LOGGER_NAME: Final[str] = "asbflow"
# Default logger level used by helper configuration.
DEFAULT_ASBFLOW_LOG_LEVEL: Final[int] = logging.INFO


def get_asbflow_logger(module_name: str | None = None) -> logging.Logger:
    """Return a logger under the library namespace.

    Parameters
    ----------
    module_name : str | None
        Optional module name to create a child logger.

    Returns
    -------
    logging.Logger
        Library logger instance.
    """
    base: str = ASBFLOW_LOGGER_NAME
    if not module_name:
        return logging.getLogger(base)

    normalized: str = module_name
    if normalized.startswith("asbflow."):
        normalized = normalized[len("asbflow.") :]

    if not normalized:
        return logging.getLogger(base)
    return logging.getLogger(f"{base}.{normalized}")


def configure_asbflow_logging(
    level: int = DEFAULT_ASBFLOW_LOG_LEVEL,
    *,
    add_stream_handler: bool = False,
) -> logging.Logger:
    """Configure the base asbflow logger.

    Parameters
    ----------
    level : int
        Logging level for the base asbflow logger.
    add_stream_handler : bool
        If ``True``, attach a basic ``StreamHandler`` when no handlers exist.

    Returns
    -------
    logging.Logger
        Configured base logger.
    """
    logger = get_asbflow_logger()
    logger.setLevel(level)

    if add_stream_handler and not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        formatter.converter = time.gmtime  # UTC timezone
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


__all__ = [
    "DEFAULT_MAX_MESSAGE_COUNT",
    "DEFAULT_DLQ_READ_MAX_MESSAGE_COUNT",
    "DEFAULT_DLQ_PURGE_MAX_MESSAGE_COUNT",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_PUBLISH_THREAD_POOL_MAX_WORKERS",
    "DEFAULT_CONSUME_THREAD_POOL_MAX_WORKERS",
    "ASBSDKImportMode",
    "DEFAULT_ASB_SDK_IMPORT_MODE",
    "ASBFLOW_LOGGER_NAME",
    "DEFAULT_ASBFLOW_LOG_LEVEL",
    "get_asbflow_logger",
    "configure_asbflow_logging",
]
