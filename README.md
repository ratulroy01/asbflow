# asbflow

`asbflow` is a Python library built on top of the Microsoft Azure Service Bus SDK that abstracts the most common messaging workflows.

## Workflow Status

[![Dev CI](https://github.com/iFoxz17/asbflow/actions/workflows/dev.yml/badge.svg)](https://github.com/iFoxz17/asbflow/actions/workflows/dev.yml)
[![Main CI](https://github.com/iFoxz17/asbflow/actions/workflows/main.yml/badge.svg)](https://github.com/iFoxz17/asbflow/actions/workflows/main.yml)
[![Release](https://github.com/iFoxz17/asbflow/actions/workflows/release.yml/badge.svg)](https://github.com/iFoxz17/asbflow/actions/workflows/release.yml)

It provides a clean service API for:
- publishing to topics and queues,
- consuming from subscriptions and queues,
- managing dead-letter queue (DLQ) operations.

The library is model-agnostic by default and integrates with Pydantic parsing when you want typed payload validation.

## Why asbflow

- Keep Azure Service Bus integration explicit but compact.
- Reuse the same high-level APIs across projects.
- Control parse behavior and settlement behavior per call.
- Use strategy-based execution (`sequential`, `thread_pool`, `async`) without changing business code.

## Core Components

- `ASBPublisher`: publish payloads (`dict` or Pydantic models).
- `ASBConsumer`: consume (settling) or read (non-settling) messages.
- `ASBDLQManager`: read/consume/redrive/purge DLQ messages.
- `ASBClientProvider`: pluggable auth provider (connection string or managed identity).
- Entity abstraction: topic/queue sender and receiver access via dedicated entity clients.

## Installation

```bash
pip install asbflow
```

For local development:

```bash
pip install -e .[dev]
```

For notebook quickstarts:

```bash
pip install -e .[notebook]
```

## Quick Start

```python
from asbflow import (
    ASBConnectionConfig,
    ASBConsumer,
    ASBConsumerConfig,
    ASBPublisher,
    ASBPublisherConfig,
)

connection = ASBConnectionConfig(
    connection_string="<connection-string>",
)

publisher = ASBPublisher(
    connection=connection,
    publisher=ASBPublisherConfig(topic_name="<topic-name>"),
)

consumer = ASBConsumer(
    connection=connection,
    consumer=ASBConsumerConfig(
        topic_name="<topic-name>",
        subscription_name="<subscription-name>",
    ),
)

publisher.publish(payload={"id": "a1", "severity": "high"}, parse=False)
result = consumer.consume(parse=False, raise_on_error=False)
print(result.succeeded, result.failed)
```

## Message Config

You can now override message metadata per publish call, and you can derive metadata dynamically from each payload.

```python
from asbflow import ASBMessageConfig, ASBDynamicMessageConfig, MessageFieldMapping

# static per-call override
publisher.publish(
    payload={"id": "a1", "severity": "high"},
    message=ASBMessageConfig(message_id="fixed-id", subject="alerts"),
)

# dynamic per-payload metadata
dynamic_message = ASBDynamicMessageConfig(
    message_id=MessageFieldMapping(lambda payload: payload["id"] if isinstance(payload, dict) else None),
    subject=MessageFieldMapping(lambda payload: payload["severity"] if isinstance(payload, dict) else None),
)

publisher.publish(
    payload=[
        {"id": "a1", "severity": "high"},
        {"id": "a2", "severity": "critical"},
    ],
    chunk_size=1,
    message=dynamic_message,
)
```

A richer walkthrough is available in [`quickstart/`](quickstart/README.md), including [`quickstart/asbflow_quickstart.ipynb`](quickstart/asbflow_quickstart.ipynb).

## Public API Snapshot

- `ASBMessageConfig`: concrete Service Bus message metadata.
- `ASBDynamicMessageConfig`: payload-driven message metadata template.
- `MessageFieldMapping`: extractor wrapper used by dynamic message config fields.
- `MessageConfigInput`: alias of `ASBMessageConfig | ASBDynamicMessageConfig` (in `asbflow.config.message`).

## Design Principles

- Abstraction over boilerplate, not over behavior.
- Safe defaults with explicit overrides.
- Uniform result contracts (`succeeded`, `failed`, `successes`, `failures`).
- Structured logging across services and strategies.

## Development

Run tests:

```bash
pytest -q test/unit
```

Build package:

```bash
python -m build
```

## CI/CD Branch Model

The repository ships with branch-oriented GitHub Actions:
- `dev`: fast CI feedback (tests + quality checks).
- `main`: full CI matrix + package build verification.
- `release`: release validation and publish workflow.

## Roadmap

The active roadmap and release follow-ups are tracked in [TODO.md](TODO.md).

## License

MIT. See [LICENSE](LICENSE).
