import pytest
from fastapi.testclient import TestClient

from order_exception_captain.api import create_app
from order_exception_captain.operator_access import (
    AdminAccess,
    OperatorAccess,
    OperatorAccessConfigurationError,
    require_access_for_host,
)


TOKEN = "test-operator-token-at-least-16-characters"
ADMIN_TOKEN = "test-admin-token-at-least-16-characters"


def test_token_protects_operator_endpoints_but_not_the_dashboard_shell(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "incidents.sqlite3", operator_token=TOKEN))

    assert client.get("/health").json() == {
        "status": "ok",
        "operator_access": "token_required",
        "admin_access": "not_configured",
        "woocommerce_connector": "not_configured",
    }
    assert client.get("/").status_code == 200
    blocked = client.get("/incidents")
    wrong = client.get("/incidents", headers={"Authorization": "Bearer wrong-token"})
    allowed = client.get("/incidents", headers={"Authorization": f"Bearer {TOKEN}"})

    assert blocked.status_code == 401
    assert blocked.headers["www-authenticate"] == "Bearer"
    assert wrong.status_code == 401
    assert allowed.status_code == 200
    assert allowed.json() == []


def test_non_local_bind_requires_a_strong_operator_token() -> None:
    with pytest.raises(OperatorAccessConfigurationError, match="requires OEC_OPERATOR_TOKEN"):
        require_access_for_host("0.0.0.0", OperatorAccess.from_token(None))
    with pytest.raises(OperatorAccessConfigurationError, match="at least 16"):
        OperatorAccess.from_token("too-short")

    require_access_for_host("127.0.0.1", OperatorAccess.from_token(None))
    require_access_for_host("0.0.0.0", OperatorAccess.from_token(TOKEN))


def test_admin_token_is_separate_from_operator_access() -> None:
    access = AdminAccess.from_token(ADMIN_TOKEN)

    assert access.authorizes(ADMIN_TOKEN)
    assert not access.authorizes(TOKEN)
    with pytest.raises(OperatorAccessConfigurationError, match="OEC_ADMIN_TOKEN"):
        AdminAccess.from_token("too-short")
