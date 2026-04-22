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


def test_connection_config_requires_namespace_for_default_azure_credential_auth():
    with pytest.raises(ValueError, match="fully_qualified_namespace is required"):
        ASBConnectionConfig(auth_method=ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL)


def test_connection_config_requires_namespace_for_client_secret_credential_auth():
    with pytest.raises(ValueError, match="fully_qualified_namespace is required"):
        ASBConnectionConfig(auth_method=ASBAuthMethod.CLIENT_SECRET_CREDENTIAL)


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


def test_connection_config_maps_legacy_managed_identity_client_id_to_client_id():
    config = ASBConnectionConfig(
        auth_method=ASBAuthMethod.MANAGED_IDENTITY,
        fully_qualified_namespace="ns.servicebus.windows.net",
        managed_identity_client_id="legacy-client-id",
    )
    assert config.client_id == "legacy-client-id"


def test_connection_config_prefers_client_id_over_legacy_managed_identity_client_id():
    config = ASBConnectionConfig(
        auth_method=ASBAuthMethod.MANAGED_IDENTITY,
        fully_qualified_namespace="ns.servicebus.windows.net",
        client_id="new-client-id",
        managed_identity_client_id="legacy-client-id",
    )
    assert config.client_id == "new-client-id"


def test_connection_config_builds_token_kwargs_for_default_azure_credential():
    credential = object()
    config = ASBConnectionConfig(
        auth_method=ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL,
        fully_qualified_namespace="ns.servicebus.windows.net",
        logging_enable=True,
        credential=credential,
    )

    kwargs = config.to_token_credential_client_kwargs(credential=credential)

    assert kwargs["fully_qualified_namespace"] == "ns.servicebus.windows.net"
    assert kwargs["credential"] is credential
    assert kwargs["logging_enable"] is True


def test_connection_config_rejects_missing_client_secret_fields_without_credential():
    with pytest.raises(ValueError, match="client_secret_tenant_id, client_id"):
        ASBConnectionConfig(
            auth_method=ASBAuthMethod.CLIENT_SECRET_CREDENTIAL,
            fully_qualified_namespace="ns.servicebus.windows.net",
            client_id="client-id",
        )


def test_connection_config_builds_client_secret_credential_kwargs():
    config = ASBConnectionConfig(
        auth_method=ASBAuthMethod.CLIENT_SECRET_CREDENTIAL,
        fully_qualified_namespace="ns.servicebus.windows.net",
        client_secret_tenant_id="tenant-id",
        client_id="client-id",
        client_secret_client_secret="client-secret",
    )

    kwargs = config.to_client_secret_credential_kwargs()

    assert kwargs == {
        "tenant_id": "tenant-id",
        "client_id": "client-id",
        "client_secret": "client-secret",
    }


def test_connection_config_rejects_wrong_builder_for_auth_mode():
    cfg = ASBConnectionConfig(connection_string="Endpoint=sb://test/")
    with pytest.raises(ValueError, match="to_token_credential_client_kwargs"):
        cfg.to_managed_identity_client_kwargs(credential=object())


def test_auth_method_parse_accepts_new_aliases():
    assert ASBAuthMethod.parse("default_credential") is ASBAuthMethod.DEFAULT_AZURE_CREDENTIAL
    assert ASBAuthMethod.parse("csc") is ASBAuthMethod.CLIENT_SECRET_CREDENTIAL
