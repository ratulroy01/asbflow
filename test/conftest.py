from __future__ import annotations

from _pytest.config import Config


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "unit: unit-level tests (single components behaviour)")
    config.addinivalue_line(
        "markers",
        "integration: integration-level tests (full library workflow, may use filesystem, network or be slow)",
    )
