from __future__ import annotations

from typing import Any


def decode_message_body(raw_message: Any) -> str:
    body: Any = raw_message.body

    if isinstance(body, bytes):
        return body.decode("utf-8")
    if isinstance(body, str):
        return body

    return b"".join(body).decode("utf-8")


__all__ = ["decode_message_body"]
