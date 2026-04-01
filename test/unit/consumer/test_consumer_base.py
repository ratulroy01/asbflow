import pytest

from asbflow.shared.message import decode_message_body


class _BodyMessage:
    def __init__(self, body):
        self.body = body


def test_decode_message_body_bytes_string_and_iterable():
    assert decode_message_body(_BodyMessage(b"abc")) == "abc"
    assert decode_message_body(_BodyMessage("abc")) == "abc"
    assert decode_message_body(_BodyMessage([b"a", b"b", b"c"])) == "abc"


def test_parser_invalid_json_returns_failure(alert_message_parser):
    result = alert_message_parser.parse_json('{"id":')

    assert result.failed is True
    assert result.succeeded is False
    assert result.payload is None
    assert result.error is not None


def test_parser_invalid_schema_returns_failure(base_payload, alert_message_parser):
    invalid_payload = dict(base_payload)
    invalid_payload.pop("alert")

    result = alert_message_parser.parse_dict(invalid_payload)

    assert result.failed is True
    assert result.payload is None
    assert result.error is not None


def test_parser_valid_returns_model(valid_payload_json, alert_message_parser):
    result = alert_message_parser.parse_json(valid_payload_json)

    assert result.succeeded is True
    assert result.failed is False
    assert result.payload is not None
    assert result.error is None
    assert result.payload.id == "msg-1"


def test_decode_invalid_bytes_raises_unicode_error():
    with pytest.raises(UnicodeDecodeError):
        decode_message_body(_BodyMessage(b"\xff\xfe\xfd"))
