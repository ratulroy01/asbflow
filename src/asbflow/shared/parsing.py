from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, NamedTuple

from pydantic import BaseModel, ValidationError

from asbflow.shared.message import decode_message_body


@dataclass(frozen=True, slots=True)
class ModelParseResult:
    payload: BaseModel | None = None
    error: Exception | None = None

    @property
    def successes(self) -> list[BaseModel]:
        return [self.payload] if self.payload is not None else []

    @property
    def failures(self) -> list[Exception]:
        return [self.error] if self.error is not None else []

    @property
    def succeeded(self) -> bool:
        return self.payload is not None and self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None


class DecodedJsonMessage(NamedTuple):
    payload: dict[str, Any] | None
    message_body: str | None
    error: Exception | None

    @property
    def succeeded(self) -> bool:
        return self.error is None and self.payload is not None

    @property
    def failed(self) -> bool:
        return not self.succeeded


class PydanticModelParser:
    def __init__(
        self,
        models: type[BaseModel] | Iterable[type[BaseModel]],
    ) -> None:
        if isinstance(models, type):
            normalized: tuple[type[BaseModel], ...] = (models,)
        else:
            normalized = tuple(models)

        if not normalized:
            raise ValueError("models must contain at least one Pydantic model")

        self._models: tuple[type[BaseModel], ...] = normalized

    @property
    def models(self) -> tuple[type[BaseModel], ...]:
        return self._models

    def parse_dict(self, payload: dict[str, Any]) -> ModelParseResult:
        last_exc: ValidationError | None = None
        for model in self._models:
            try:
                return ModelParseResult(payload=model.model_validate(payload))
            except ValidationError as exc:
                last_exc = exc

        if last_exc is not None:
            return ModelParseResult(error=last_exc)

        return ModelParseResult(error=ValueError("No parser model configured"))

    def parse_json(self, payload_json: str) -> ModelParseResult:
        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except Exception as exc:
            return ModelParseResult(error=exc)
        return self.parse_dict(payload)


def decode_json_message(raw_message: Any) -> DecodedJsonMessage:
    message_body: str | None = None
    try:
        message_body = decode_message_body(raw_message)
        payload: dict[str, Any] = json.loads(message_body)
        return DecodedJsonMessage(payload=payload, message_body=message_body, error=None)
    except Exception as exc:
        return DecodedJsonMessage(payload=None, message_body=message_body, error=exc)


__all__ = [
    "ModelParseResult",
    "DecodedJsonMessage",
    "PydanticModelParser",
    "decode_json_message",
]
