# Quickstart

This folder expands the [Quick Start section in README](../README.md#quick-start) with a runnable notebook.

## Files

- `asbflow_quickstart.ipynb`: end-to-end publish/consume/read/DLQ quickstart with optional Pydantic parsing, redrive, and execution-mode examples.

## Message Config Example (1.0.2)

Use per-call message metadata overrides, including dynamic values extracted from each payload.

```python
from asbflow import ASBMessageConfig, ASBDynamicMessageConfig, MessageFieldMapping

# static override
publisher.publish(
    {"id": "msg-1", "severity": "high"},
    message=ASBMessageConfig(subject="quickstart-static", message_id="msg-1"),
)

# dynamic mapping by payload
dynamic_message = ASBDynamicMessageConfig(
    message_id=MessageFieldMapping(lambda payload: payload["id"] if isinstance(payload, dict) else None),
    subject=MessageFieldMapping(lambda payload: payload["severity"] if isinstance(payload, dict) else None),
)

publisher.publish(
    [
        {"id": "msg-1", "severity": "high"},
        {"id": "msg-2", "severity": "critical"},
    ],
    chunk_size=1,
    message=dynamic_message,
)
```

## Run locally

1. Install dependencies:

```bash
pip install -e ".[dev,notebook]"
```

2. Export these environment variables:

- `ASB_CONNECTION_STRING`
- `ASB_TOPIC_NAME`
- `ASB_SUBSCRIPTION_NAME`

3. Open the notebook:

```bash
jupyter lab quickstart/asbflow_quickstart.ipynb
```

The notebook keeps live operations disabled by default (`RUN_LIVE = False`) so you can review it safely first.
