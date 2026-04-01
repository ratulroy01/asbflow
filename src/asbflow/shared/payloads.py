from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from asbflow.shared.parsing import ModelParseResult, PydanticModelParser

PayloadMapping = dict[str, object]
PublishablePayload = BaseModel | PayloadMapping
PublishInput = PublishablePayload | list[PublishablePayload]


class PayloadNormalizer:
    def __init__(self, parser: PydanticModelParser | None = None) -> None:
        self._parser: PydanticModelParser | None = parser

    @property
    def parser(self) -> PydanticModelParser | None:
        return self._parser

    @property
    def parser_or_raise(self) -> PydanticModelParser:
        if self._parser is None:
            raise ValueError("A parser is required when parse=True")
        return self._parser

    def resolve_parser(
        self,
        parser: PydanticModelParser | None = None,
    ) -> PydanticModelParser:
        if parser is not None:
            return parser
        return self.parser_or_raise

    def parse_dict(
        self,
        payload: dict[str, Any],
        *,
        parser: PydanticModelParser | None = None,
    ) -> ModelParseResult:
        return self.resolve_parser(parser).parse_dict(payload)

    def normalize_payload(
        self,
        payload: PublishablePayload,
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> PublishablePayload:
        if isinstance(payload, BaseModel):
            return payload

        if not parse:
            return payload

        parse_result = self.parse_dict(dict(payload), parser=parser)
        if parse_result.error is not None:
            raise parse_result.error
        if parse_result.payload is None:
            raise ValueError("Parser did not produce a payload")

        return parse_result.payload

    def normalize_payloads(
        self,
        payloads: list[PublishablePayload],
        *,
        parse: bool = False,
        parser: PydanticModelParser | None = None,
    ) -> list[PublishablePayload]:
        return [self.normalize_payload(payload, parse=parse, parser=parser) for payload in payloads]


__all__ = [
    "PayloadMapping",
    "PublishablePayload",
    "PublishInput",
    "PayloadNormalizer",
]
