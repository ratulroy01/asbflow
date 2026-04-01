# TODO

## Pre-release Checklist

- [ ] Confirm `project.version` in `pyproject.toml` is bumped.
- [ ] Run local checks (`pytest`, `black --check`, `isort --check-only`).
- [ ] Run `pre-commit run --all-files`.
- [ ] Verify `CHANGELOG.md` includes release notes for the target version.
- [ ] Push to `release` branch and verify `create-tag` created `v<version>`.
- [ ] Verify `publish-auto` succeeded and package is visible on PyPI.

## Follow-ups

- [ ] Add TestPyPI publish job before production PyPI publish.
- [ ] Add smoke test that installs built wheel in a clean environment.
- [ ] Add workflow badge/status section to README.
- [ ] Implement integration-tests and add strategy documentation (live ASB tests vs unit tests).
