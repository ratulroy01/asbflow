# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [1.0.3] - 2026-04-22

### Added
- Added `DefaultAzureCredentialClientProvider` and `ClientSecretCredentialClientProvider`.
- Added `default_azure_credential` and `client_secret_credential` in `ASBAuthMethod`.

### Changed
- `ASBClientProviderFactory` now resolves providers for all supported auth methods.
- `ASBConnectionConfig` now supports shared token-credential kwargs generation and client-secret credential kwargs generation.
- `ASBConnectionConfig` now standardizes on `client_id`; legacy `managed_identity_client_id` is still accepted at init-time for backward compatibility and mapped in `__post_init__`.

## [1.0.2] - 2026-04-03

### Added
- Dynamic message metadata support via `ASBDynamicMessageConfig` and `MessageFieldMapping`.
- New message-config module (`asbflow.config.message`) containing message metadata models and aliases.

### Changed
- `ASBPublisher.publish*` methods now accept per-call `message` overrides.
- Strategy-specific message-config builders now resolve concrete `ASBMessageConfig` per payload.
- `ASBConsumer.aconsume` now directly invokes async strategy `aconsume` (no thread wrapper).
- Shared override resolution utility (`PropertyResolver`) is used consistently in publisher, consumer and DLQ paths.

### Fixed
- Publisher strategy constructor typing now uses explicit typed optional dependencies, removing static type-checking errors from untyped `**kwargs`.

## [1.0.1] - 2026-04-01

### Changed
- Metadata support for Python 3.13 and 3.14.

## [1.0.0] - 2026-04-01

### Added
- Initial public-ready package scaffold for `asbflow`.
- Topic/queue abstraction for publisher and consumer strategies.
- Auth provider abstraction with connection-string and managed-identity implementations.
- Factory-based service construction for publisher, consumer, and DLQ manager.
- Structured result objects with uniform success/failure properties.
- GitHub community and CI/CD templates for `dev`, `main`, and `release` branch workflows.
