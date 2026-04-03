from datetime import datetime, timedelta, timezone

from asbflow.config.message import (
    ASBDynamicMessageConfig,
    ASBMessageConfig,
    MessageFieldMapping,
)


def test_message_config_to_message_kwargs_includes_optional_and_extra():
    config = ASBMessageConfig(
        content_type="application/json",
        message_id="mid",
        subject="subject",
        time_to_live=timedelta(minutes=1),
        scheduled_enqueue_time_utc=datetime(2026, 3, 23, 12, 0, tzinfo=timezone.utc),
        application_properties={"k": "v"},
        message_kwargs={"session_id": "sid"},
    )

    kwargs = config.to_message_kwargs()

    assert kwargs["content_type"] == "application/json"
    assert kwargs["message_id"] == "mid"
    assert kwargs["subject"] == "subject"
    assert kwargs["time_to_live"] == timedelta(minutes=1)
    assert kwargs["scheduled_enqueue_time_utc"] == datetime(2026, 3, 23, 12, 0, tzinfo=timezone.utc)
    assert kwargs["application_properties"] == {"k": "v"}
    assert kwargs["session_id"] == "sid"


def test_extended_message_config_resolves_from_dict_payload(base_payload):
    config = ASBDynamicMessageConfig(
        message_id=MessageFieldMapping(
            lambda message: message["id"] if isinstance(message, dict) and isinstance(message["id"], str) else None
        ),
        subject=MessageFieldMapping(
            lambda message: message["alert"]["name"] if isinstance(message, dict) else None  # type: ignore
        ),  # type: ignore
        message_kwargs=MessageFieldMapping(
            lambda message: {"reply_to": message["system"]} if isinstance(message, dict) else {}
        ),
    )

    resolved = config.to_message_config(base_payload)

    assert resolved.message_id == "msg-1"
    assert resolved.subject == "Test alert"
    assert resolved.message_kwargs["reply_to"] == "Pegaso"


def test_extended_message_config_resolves_from_pydantic_payload(alert_message):
    config = ASBDynamicMessageConfig(
        message_id=MessageFieldMapping(lambda message: getattr(message, "id", None)),
        subject=MessageFieldMapping(lambda message: getattr(message, "alert", {}).get("name")),
    )

    resolved = config.to_message_config(alert_message)

    assert resolved.message_id == "msg-1"
    assert resolved.subject == "Test alert"
