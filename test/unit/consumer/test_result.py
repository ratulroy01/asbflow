from asbflow.consumer.result import (
    ConsumedPayloadFailure,
    ConsumeError,
    ParsedConsumeResult,
)


def test_consume_result_properties(alert_message):
    failure = ConsumedPayloadFailure(error=ValueError("boom"), message_body="{}")
    result = ParsedConsumeResult(parsed_messages=[alert_message], errors=[failure])

    assert result.successes == [alert_message]
    assert result.failures == [failure]
    assert result.failed is True


def test_consume_errors_found_error_keeps_result(alert_message):
    result = ParsedConsumeResult(
        parsed_messages=[alert_message],
        errors=[ConsumedPayloadFailure(error=ValueError("x"))],
    )

    exc = ConsumeError(result)

    assert exc.result is result
    assert "1 consume errors" in str(exc)
