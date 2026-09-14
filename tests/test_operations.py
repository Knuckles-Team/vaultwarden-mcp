"""Coverage for the generated Vaultwarden operation surface.

Exercises the ``ROUTES`` catalog (``_routes.py``), the generated domain
mixins + dispatch (``api_client_operations.py``), the derived MCP manifest
(``_operation_manifest.py``), and their wiring into the fleet's verbose
1:1 MCP tool surface (``agent_utilities.mcp.verbose_tools``).
"""

from __future__ import annotations

from collections import Counter
from typing import Any
from unittest.mock import MagicMock

import pytest
from agent_utilities.mcp.verbose_tools import _domain_methods

from vaultwarden_mcp.api._operation_manifest import OPERATIONS, OPERATIONS_BY_NAME
from vaultwarden_mcp.api._routes import ROUTES, Route
from vaultwarden_mcp.api.api_client_operations import (
    VaultwardenApi,
    VaultwardenApiOperationsBase,
    _substitute_path,
)

#: Handlers excluded by the documented rules (non-agent-API-operation domains,
#: SSO browser callbacks, the base-owned login grant, and admin HTML renders).
#: None of these collide with a *kept* route's final (possibly renamed) name.
EXCLUDED_HANDLER_NAMES = (
    "admin_disabled",
    "admin_page",
    "admin_page_login",
    "post_admin_login",
    "logout",
    "users_overview",
    "organizations_overview",
    "diagnostics",
    "login",
    "oidcsignin",
    "oidcsignin_error",
    "authorize",
    "web_index",
    "web_index_direct",
    "app_id",
    "apple_app_site_association",
    "web_files",
    "attachments",
    "static_files",
    "static_files_dev",
    "vaultwarden_css",
    "websockets_hub",
    "anonymous_websockets_hub",
)


def _client_with_mock_request() -> Any:
    # Typed as ``Any``: the generated per-route methods are attached to the
    # domain mixins via ``setattr`` at import time, so mypy cannot see them as
    # static attributes of ``VaultwardenApi`` — and assigning over the real
    # ``request`` method for the mock double is itself only valid dynamically.
    client: Any = VaultwardenApi.__new__(VaultwardenApi)
    client.request = MagicMock(return_value={"ok": True})
    return client


def test_route_names_are_unique():
    names = [route.name for route in ROUTES]
    dupes = [name for name, count in Counter(names).items() if count > 1]
    assert dupes == []
    assert len(names) == len(ROUTES)


def test_every_route_yields_exactly_one_method_on_the_client():
    for route in ROUTES:
        assert hasattr(VaultwardenApi, route.name), f"missing method for {route.name}"
    # And nothing extra: every generated callable maps back to a route.
    generated = _domain_methods(VaultwardenApi)
    assert set(generated) == {route.name for route in ROUTES}


@pytest.mark.parametrize("handler_name", EXCLUDED_HANDLER_NAMES)
def test_excluded_routes_are_absent(handler_name):
    assert not hasattr(VaultwardenApi, handler_name)


def test_renamed_duplicates_are_disambiguated_by_domain():
    # Handler names that collided across domains were prefixed with the
    # domain slug so both survive under distinct, unique names.
    for name in (
        "accounts_post_prelogin",
        "identity_post_prelogin",
        "accounts_post_api_key",
        "organizations_post_api_key",
        "accounts_rotate_api_key",
        "organizations_rotate_api_key",
        "organizations_delete_organization",
        "admin_delete_organization",
        "organizations_send_invite",
        "emergency_access_send_invite",
        "organizations_accept_invite",
        "emergency_access_accept_invite",
    ):
        assert hasattr(VaultwardenApi, name), f"expected renamed method {name}"


def test_path_substitution_quotes_path_params():
    route = Route(
        name="x",
        domain="misc",
        http_method="GET",
        path="api/things/{thing_id}",
        auth="none",
        path_params=("thing_id",),
    )
    assert _substitute_path(route, {"thing_id": "a/b c"}) == "api/things/a%2Fb%20c"


def test_path_substitution_catch_all_preserves_slashes():
    route = Route(
        name="y",
        domain="misc",
        http_method="GET",
        path="api/things/{rest}",
        auth="none",
        path_params=("rest",),
        catch_all=("rest",),
    )
    assert _substitute_path(route, {"rest": "a/b/c"}) == "api/things/a/b/c"


def test_path_substitution_raises_on_missing_required_param():
    route = Route(
        name="get_cipher",
        domain="ciphers",
        http_method="GET",
        path="api/ciphers/{cipher_id}",
        auth="user",
        path_params=("cipher_id",),
    )
    with pytest.raises(ValueError, match="cipher_id"):
        _substitute_path(route, {})


def test_missing_path_param_raises_through_the_bound_method():
    client = _client_with_mock_request()
    with pytest.raises(ValueError, match="cipher_id"):
        client.get_cipher()
    client.request.assert_not_called()


def test_bound_method_dispatches_method_path_and_auth():
    client = _client_with_mock_request()
    client.get_cipher(cipher_id="abc")
    client.request.assert_called_once_with(
        "GET",
        "api/ciphers/abc",
        auth="user",
        json_body=None,
        form=None,
        params=None,
    )


def test_bound_method_merges_query_params_and_json_body():
    client = _client_with_mock_request()
    client.get_members(org_id="o1", data="page=2", json_body={"x": 1})
    client.request.assert_called_once_with(
        "GET",
        "api/organizations/o1/users",
        auth="user",
        json_body={"x": 1},
        form=None,
        params={"data": "page=2"},
    )


def test_bound_method_passes_admin_auth():
    client = _client_with_mock_request()
    client.get_diagnostics_config()
    client.request.assert_called_once_with(
        "GET",
        "admin/diagnostics/config",
        auth="admin",
        json_body=None,
        form=None,
        params=None,
    )


def test_delete_cipher_selected_put_exists_with_put():
    route = next(r for r in ROUTES if r.name == "delete_cipher_selected_put")
    assert route.http_method == "PUT"
    assert route.path == "api/ciphers/delete"
    client = _client_with_mock_request()
    client.delete_cipher_selected_put()
    client.request.assert_called_once_with(
        "PUT",
        "api/ciphers/delete",
        auth="user",
        json_body=None,
        form=None,
        params=None,
    )


def test_every_manifest_operation_exists_on_the_client():
    assert OPERATIONS
    assert len(OPERATIONS) == len(ROUTES)
    for operation in OPERATIONS:
        assert hasattr(VaultwardenApi, operation["method"])
    assert set(OPERATIONS_BY_NAME) == {route.name for route in ROUTES}


def test_domain_methods_includes_generated_operations_and_excludes_base():
    methods = _domain_methods(VaultwardenApi)
    assert "get_cipher" in methods
    assert "delete_cipher_selected_put" in methods
    for excluded in ("request", "call_operation", "sync_vault", "soft_delete_ciphers"):
        assert excluded not in methods


def test_call_operation_dispatches_by_name():
    client = _client_with_mock_request()
    client.call_operation("get_cipher", cipher_id="abc")
    client.request.assert_called_once_with(
        "GET",
        "api/ciphers/abc",
        auth="user",
        json_body=None,
        form=None,
        params=None,
    )


def test_call_operation_rejects_unknown_names():
    client = _client_with_mock_request()
    with pytest.raises(ValueError, match="Unknown Vaultwarden operation"):
        client.call_operation("not_a_real_operation")


def test_operations_base_class_name_ends_in_base():
    # So agent_utilities.mcp.verbose_tools treats it as base infrastructure,
    # never a generated verbose tool.
    assert VaultwardenApiOperationsBase.__name__.endswith("Base")
