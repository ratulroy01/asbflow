# Contributing to asbflow

Thanks for contributing.

## Development Setup

1. Clone the repository.
2. Run the setup script for your OS:

```powershell
# Windows (PowerShell)
.\script\setup-dev.ps1
```

```bash
# Linux / macOS
bash ./script/setup-dev.sh
```

These scripts create a virtual environment (if needed), install development dependencies (`-e .[dev]`), and install `pre-commit` hooks.

## Local Checks

Run before opening a PR:

```powershell
# Windows (PowerShell)
.\script\run-local-checks.ps1
```

```bash
# Linux / macOS
bash ./script/run-local-checks.sh
```

You can also run pre-commit hooks on all files:

```bash
pre-commit run --all-files
```

## Branching Model

- `features/<feature_name>`: branch from `dev` to develop new features.
- `dev`: integration branch for day-to-day development.
- `main`: stable branch.
- `release`: release hardening and publishing branch.

## Pull Requests

- Keep PRs focused and small when possible.
- Add or update tests for behavioral changes.
- Update docs when public APIs change.
- Reference related issues in the PR description.
