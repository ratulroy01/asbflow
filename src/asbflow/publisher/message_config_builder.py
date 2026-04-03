from __future__ import annotations

from asbflow.config.message import ASBDynamicMessageConfig, ASBMessageConfig, MessageConfigInput
from asbflow.shared.payloads import PublishablePayload
from asbflow.shared.resolution import PropertyResolver


class MessageConfigBuilder:
    """Resolve per-call and per-payload message configuration."""

    def __init__(self, default_message_config: MessageConfigInput | None = None) -> None:
        self._resolver: PropertyResolver[MessageConfigInput] = PropertyResolver(
            default_message_config or ASBMessageConfig()
        )

    @property
    def default(self) -> MessageConfigInput:
        return self._resolver.default

    def resolve(self, override: MessageConfigInput | None = None) -> MessageConfigInput:
        return self._resolver.resolve(override)

    def build(
        self,
        payload: PublishablePayload,
        override: MessageConfigInput | None = None,
    ) -> ASBMessageConfig:
        resolved: MessageConfigInput = self.resolve(override)
        if isinstance(resolved, ASBDynamicMessageConfig):
            return resolved.to_message_config(payload)
        return resolved


__all__ = ["MessageConfigBuilder"]
