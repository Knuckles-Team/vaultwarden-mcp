"""Composite Vaultwarden client: base transport plus one mixin per API domain.

Every callable operation is generated at import time from the :data:`ROUTES`
catalog (``_routes.py``) — one bound method per :class:`~vaultwarden_mcp.api
._routes.Route`, attached to the domain mixin class named after its
``Route.domain``. Nothing here is hand-written per endpoint: adding, renaming,
or retiring a Vaultwarden operation is a change to ``_routes.py`` only.

Each generated method accepts its path parameters as required keyword-only
arguments, its declared query placeholders as optional keyword-only arguments,
and the generic ``json_body``/``params``/``form`` passthrough accepted by
:meth:`~vaultwarden_mcp.api.api_client_base.VaultwardenApiBase.request`.
"""

from __future__ import annotations

import inspect
from typing import Any
from urllib.parse import quote

from ._routes import ROUTES, Route
from .api_client_base import VaultwardenApiBase


def _substitute_path(route: Route, values: dict[str, Any]) -> str:
    """Render ``route.path`` with its ``{name}`` placeholders URL-quoted in.

    Raises ``ValueError`` naming the parameter when a required path
    parameter is absent or ``None``. A catch-all path parameter (one listed
    in ``route.catch_all``) is quoted with ``safe="/"`` so it may itself
    contain path separators; every other path parameter is quoted with
    ``safe=""``.
    """
    path = route.path
    for name in route.path_params:
        value = values.get(name)
        if value is None:
            raise ValueError(
                f"{route.name}() is missing required path parameter {name!r}"
            )
        safe = "/" if name in route.catch_all else ""
        path = path.replace("{" + name + "}", quote(str(value), safe=safe))
    return path


def _build_signature(route: Route) -> inspect.Signature:
    """A real ``inspect.Signature`` for ``route`` so introspection (``help()``,
    ``inspect.signature``, IDE completion) shows the actual parameters."""
    parameters: list[inspect.Parameter] = [
        inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
    ]
    for name in route.path_params:
        parameters.append(
            inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, annotation=str)
        )
    for name in route.query_params:
        parameters.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Any,
            )
        )
    for extra in ("json_body", "params", "form"):
        parameters.append(
            inspect.Parameter(
                extra,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Any,
            )
        )
    return inspect.Signature(parameters, return_annotation=Any)


def _build_doc(route: Route) -> str:
    lines = [route.summary or f"Invoke the {route.name} operation."]
    lines.append("")
    lines.append(f"``{route.http_method} /{route.path}``")
    lines.append(f"Auth: {route.auth}.")
    if route.destructive:
        lines.append("Destructive.")
    return "\n".join(lines)


def _make_operation(route: Route) -> Any:
    """Build the bound method implementing ``route``."""

    def operation(self: Any, **kwargs: Any) -> Any:
        json_body = kwargs.pop("json_body", None)
        params = kwargs.pop("params", None)
        form = kwargs.pop("form", None)
        path = _substitute_path(route, kwargs)
        query: dict[str, Any] = dict(params) if params else {}
        for name in route.query_params:
            value = kwargs.pop(name, None)
            if value is not None:
                query.setdefault(name, value)
        return self.request(
            route.http_method,
            path,
            auth=route.auth,
            json_body=json_body,
            form=form,
            params=query or None,
        )

    operation.__name__ = route.name
    operation.__qualname__ = f"{_DOMAIN_CLASS_NAMES[route.domain]}.{route.name}"
    operation.__doc__ = _build_doc(route)
    operation.__signature__ = _build_signature(route)  # type: ignore[attr-defined]
    return operation


class VaultwardenApiAccounts:
    """Profile, keys, devices, and login-with-device auth requests."""

    DOMAIN = "accounts"


class VaultwardenApiCiphers:
    """Vault sync plus cipher CRUD, attachments, sharing, and bulk actions."""

    DOMAIN = "ciphers"


class VaultwardenApiFolders:
    """Personal-vault folder CRUD."""

    DOMAIN = "folders"


class VaultwardenApiOrganizations:
    """Organizations, collections, members, groups, policies, and billing."""

    DOMAIN = "organizations"


class VaultwardenApiSends:
    """Bitwarden Send creation, file upload, and anonymous access."""

    DOMAIN = "sends"


class VaultwardenApiEmergencyAccess:
    """Emergency-access grants: invite, confirm, initiate/approve, takeover."""

    DOMAIN = "emergency_access"


class VaultwardenApiTwoFactor:
    """Two-factor methods: authenticator, Duo, email, WebAuthn, YubiKey."""

    DOMAIN = "two_factor"


class VaultwardenApiEvents:
    """Audit event feeds for an org, a cipher, or an org member."""

    DOMAIN = "events"


class VaultwardenApiIdentity:
    """Identity-server operations other than the OAuth2 token grant itself."""

    DOMAIN = "identity"


class VaultwardenApiAdmin:
    """Instance admin-panel JSON operations (cookie auth)."""

    DOMAIN = "admin"


class VaultwardenApiIcons:
    """Favicon fetch/serve for autofill matching."""

    DOMAIN = "icons"


class VaultwardenApiPublic:
    """The org API-key-scoped public API."""

    DOMAIN = "public"


class VaultwardenApiMisc:
    """Meta endpoints: equivalent domains, HIBP proxy, server info."""

    DOMAIN = "misc"


#: ``Route.domain`` slug -> the mixin class it contributes methods to.
_DOMAIN_CLASSES: dict[str, type] = {
    VaultwardenApiAccounts.DOMAIN: VaultwardenApiAccounts,
    VaultwardenApiCiphers.DOMAIN: VaultwardenApiCiphers,
    VaultwardenApiFolders.DOMAIN: VaultwardenApiFolders,
    VaultwardenApiOrganizations.DOMAIN: VaultwardenApiOrganizations,
    VaultwardenApiSends.DOMAIN: VaultwardenApiSends,
    VaultwardenApiEmergencyAccess.DOMAIN: VaultwardenApiEmergencyAccess,
    VaultwardenApiTwoFactor.DOMAIN: VaultwardenApiTwoFactor,
    VaultwardenApiEvents.DOMAIN: VaultwardenApiEvents,
    VaultwardenApiIdentity.DOMAIN: VaultwardenApiIdentity,
    VaultwardenApiAdmin.DOMAIN: VaultwardenApiAdmin,
    VaultwardenApiIcons.DOMAIN: VaultwardenApiIcons,
    VaultwardenApiPublic.DOMAIN: VaultwardenApiPublic,
    VaultwardenApiMisc.DOMAIN: VaultwardenApiMisc,
}
_DOMAIN_CLASS_NAMES: dict[str, str] = {
    domain: cls.__name__ for domain, cls in _DOMAIN_CLASSES.items()
}

_ROUTES_BY_NAME: dict[str, Route] = {}
for _route in ROUTES:
    setattr(_DOMAIN_CLASSES[_route.domain], _route.name, _make_operation(_route))
    _ROUTES_BY_NAME[_route.name] = _route
del _route


class VaultwardenApiOperationsBase:
    """Dispatch a :data:`~vaultwarden_mcp.api._routes.ROUTES` operation by name.

    Never an API operation itself (its name ends in ``Base``, so
    ``agent_utilities.mcp.verbose_tools._domain_methods`` — and therefore the
    verbose MCP tool surface — never expands it).
    """

    def call_operation(self, operation: str, **params: Any) -> Any:
        try:
            route = _ROUTES_BY_NAME[operation]
        except KeyError as exc:
            raise ValueError(f"Unknown Vaultwarden operation: {operation!r}") from exc
        method = getattr(self, route.name)
        return method(**params)


class VaultwardenApi(
    VaultwardenApiAccounts,
    VaultwardenApiCiphers,
    VaultwardenApiFolders,
    VaultwardenApiOrganizations,
    VaultwardenApiSends,
    VaultwardenApiEmergencyAccess,
    VaultwardenApiTwoFactor,
    VaultwardenApiEvents,
    VaultwardenApiIdentity,
    VaultwardenApiAdmin,
    VaultwardenApiIcons,
    VaultwardenApiPublic,
    VaultwardenApiMisc,
    VaultwardenApiOperationsBase,
    VaultwardenApiBase,
):
    """The client every tool receives: every domain mixin plus dispatch and transport."""
