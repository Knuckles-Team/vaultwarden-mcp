"""Normalized MCP operation manifest, derived from :data:`~vaultwarden_mcp.api
._routes.ROUTES` at import time.

Consumed by ``agent_utilities.mcp.verbose_tools.register_verbose_tools`` (the
``manifest=`` argument) to synthesize a fully-typed verbose MCP tool per
operation instead of falling back to the generic ``params_json`` tool.
"""

from __future__ import annotations

from typing import Any

from ._routes import ROUTES

_BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_FORM_PATH_PREFIXES = ("identity/", "admin/")


def _params_for(route: Any) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = [
        {
            "name": name,
            "type": "string",
            "required": True,
            "description": f"Path parameter '{name}'.",
        }
        for name in route.path_params
    ]
    params.extend(
        {
            "name": name,
            "type": "string",
            "required": False,
            "description": f"Query parameter '{name}'.",
        }
        for name in route.query_params
    )
    if route.http_method in _BODY_METHODS:
        params.append(
            {
                "name": "json_body",
                "type": "object",
                "required": False,
                "description": "JSON request body.",
            }
        )
    params.append(
        {
            "name": "params",
            "type": "object",
            "required": False,
            "description": "Additional query-string parameters.",
        }
    )
    if route.path.startswith(_FORM_PATH_PREFIXES):
        params.append(
            {
                "name": "form",
                "type": "object",
                "required": False,
                "description": "Form-encoded request body.",
            }
        )
    return params


OPERATIONS: list[dict[str, Any]] = [
    {
        "method": route.name,
        "domain": route.domain,
        "summary": route.summary,
        "params": _params_for(route),
    }
    for route in ROUTES
]

OPERATIONS_BY_NAME: dict[str, dict[str, Any]] = {op["method"]: op for op in OPERATIONS}
