import pytest

from asbflow.config import ASBAuthMethod, ASBConnectionConfig


def test_connection_config_connection_string_kwargs_include_optional_and_extra():
    config = ASBConnectionConfig(
        connection_string="Endpoint=sb://test/",
        logging_enable=True,
        user_agent="ua",
        http_proxy={"proxy_hostname": "proxy.local", "proxy_port": 8080},
        custom_endpoint_address="sb://custom/",
        client_kwargs={"retry_total": 5},
    )

    kwargs = config.to_connection_string_client_kwargs()

    assert kwargs["conn_str"] == "Endpoint=sb://test/"
    assert kwargs["logging_enable"] is True
    assert kwargs["user_agent"] == "ua"
    assert kwargs["custom_endpoint_address"] == "sb://custom/"
    assert kwargs["retry_total"] == 5


def test_connection_config_connection_string_kwargs_minimal():
    kwargs = ASBConnectionConfig(connection_string="Endpoint=sb://test/").to_connection_string_client_kwargs()

    assert kwargs == {
        "conn_str": "Endpoint=sb://test/",
        "logging_enable": False,
    }


def test_connection_config_requires_connection_string_for_connection_string_auth():
    with pytest.raises(ValueError, match="connection_string is required"):
        ASBConnectionConfig(auth_method=ASBAuthMethod.CONNECTION_STRING)


def test_connection_config_requires_namespace_for_managed_identity_auth():
    with pytest.raises(ValueError, match="fully_qualified_namespace is required"):
        ASBConnectionConfig(auth_method=ASBAuthMethod.MANAGED_IDENTITY)


def test_connection_config_builds_managed_identity_kwargs():
    credential = object()
    config = ASBConnectionConfig(
        auth_method=ASBAuthMethod.MANAGED_IDENTITY,
        fully_qualified_namespace="ns.servicebus.windows.net",
        logging_enable=True,
        credential=credential,
    )

    kwargs = config.to_managed_identity_client_kwargs(credential=credential)

    assert kwargs["fully_qualified_namespace"] == "ns.servicebus.windows.net"
    assert kwargs["credential"] is credential
    assert kwargs["logging_enable"] is True


def test_connection_config_rejects_wrong_builder_for_auth_mode():
    cfg = ASBConnectionConfig(connection_string="Endpoint=sb://test/")
    with pytest.raises(ValueError, match="managed_identity"):
        cfg.to_managed_identity_client_kwargs(credential=object())
