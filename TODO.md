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
 - [ ] Implement scheduled message publishing.
 - [ ] Extend automatic batch size management to account for both message count (already implemented) and total payload size in bytes (pending).
 - [ ] Implement integration-tests and add strategy documentation (live ASB tests vs unit tests).
 - [ ] Add entity lifecycle and resource management (queues, topics, subscriptions).
 - [ ] Implement advanced DLQ & retry policy automation (custom policies, delayed retries, backoff strategies).
 - [ ] Add observability: metrics, structured logging, and tracing hooks.
 - [ ] Support fine-grained batching controls (count + bytes + timing triggers).
 - [ ] Implement transactional support for atomic send + settle operations.
 - [ ] Provide local development/emulator workflows for testing without live ASB.
 - [ ] Add schema/contract management (Pydantic + Avro/Protobuf support, versioning).
 - [ ] Expose management client features: inspect metadata, quotas and access policies.
 - [ ] Provide CLI or admin tooling for quick publishing, DLQ inspection and bulk retries.
