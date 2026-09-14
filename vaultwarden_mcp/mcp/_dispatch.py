"""Shared dispatch helpers for the Vaultwarden route-backed MCP tools.

Every route-backed ``vaultwarden_<domain>`` tool (accounts, ciphers, folders,
organizations, sends, admin) shares one shape: resolve a free-form ``action``
string against a subset of :data:`~vaultwarden_mcp.api._routes.ROUTES`, gate a
destructive route behind an explicit ``confirm``, and dispatch through
``VaultwardenApi.call_operation`` off the event loop. Kept in a private module
(not re-exported from ``mcp/__init__.py``) so module auto-discovery of
``register_<domain>_tools`` never mistakes it for a tool registrar.
"""

from __future__ import annotations

import json
from typing import Any

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking

from ..api._routes import ROUTES, Route

#: Tool-facing service name used in discovery payloads and error messages.
SERVICE = "vaultwarden-mcp"


def domain_routes(*domains: str) -> dict[str, Route]:
    """``{route.name: route}`` for every :data:`ROUTES` entry in ``domains``."""
    return {route.name: route for route in ROUTES if route.domain in domains}


def parse_params(params_json: str) -> dict[str, Any]:
    """Parse ``params_json`` into a plain dict; raises on invalid input."""
    parsed = json.loads(params_json)
    if not isinstance(parsed, dict):
        raise ValueError("params_json must decode to a JSON object")
    return parsed


async def dispatch_route(
    client: Any,
    action: str,
    params: dict[str, Any],
    routes: dict[str, Route],
    *,
    service: str = SERVICE,
) -> Any:
    """Resolve ``action`` against ``routes`` and call it via ``call_operation``.

    Unknown or discovery actions return :func:`resolve_action`'s payload
    directly. A route with ``destructive=True`` is refused with an
    explanatory dict unless ``params`` carries ``confirm: true`` (the
    ``confirm`` key itself is stripped before the call is made).
    """
    resolved = resolve_action(action, routes, service=service)
    if isinstance(resolved, dict):
        return resolved
    route = routes[resolved]
    call_params = dict(params)
    confirmed = bool(call_params.pop("confirm", False))
    if route.destructive and not confirmed:
        return {
            "confirm_required": True,
            "action": resolved,
            "message": f"'{resolved}' is destructive; retry with confirm: true.",
        }
    return await run_blocking(client.call_operation, resolved, **call_params)
