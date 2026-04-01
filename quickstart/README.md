# Quickstart

This folder expands the [Quick Start section in README](../README.md#quick-start) with a runnable notebook.

## Files

- `asbflow_quickstart.ipynb`: end-to-end publish/consume/read/DLQ quickstart with optional Pydantic parsing, redrive, and execution-mode examples.

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
