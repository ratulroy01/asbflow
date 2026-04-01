import json

import pytest
from pydantic import BaseModel

from asbflow.shared.parsing import PydanticModelParser


class _ModelA(BaseModel):
    id: str


class _ModelB(BaseModel):
    code: int


def test_parser_supports_multiple_models():
    parser = PydanticModelParser([_ModelA, _ModelB])

    result = parser.parse_json(json.dumps({"code": 42}))

    assert result.payload is not None
    assert isinstance(result.payload, _ModelB)
    assert result.payload.code == 42


def test_parser_returns_failure_for_invalid_body():
    parser = PydanticModelParser([_ModelA])

    result = parser.parse_json('{"id":')

    assert result.failed is True
    assert result.error is not None


def test_parser_requires_at_least_one_model():
    with pytest.raises(ValueError, match="at least one"):
        PydanticModelParser([])
