"""Instance admin, identity, and icon MCP tool."""

import json

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..api.api_client_base import VaultwardenApiError
from ..auth import get_client
from ._dispatch import SERVICE, dispatch_route, domain_routes, parse_params

_ROUTES = domain_routes("admin", "identity", "icons")


def register_admin_tools(mcp: FastMCP):
    """Register the instance-admin/identity/icon tool."""

    @mcp.tool(tags={"admin"})
    async def vaultwarden_admin(
        action: str = Field(
            description=(
                "Vaultwarden admin/identity/icons operation name (a "
                "Route.name). Call with action='list_actions' to list every "
                "available operation."
            )
        ),
        params_json: str = Field(
            default="{}",
            description="JSON object of path/query/body parameters for the action.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Administer the instance (users, config, diagnostics), plus
        identity-server and favicon routes.

        Admin routes require the instance admin token (``VW_ADMIN`` cookie
        auth). When it is not configured, or is rejected, the server's error
        is surfaced as a clear ``{"error", "status"}`` dict rather than a
        raw exception.

        CONCEPT:VW-ECO.mcp.admin-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_admin action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}
        try:
            return await dispatch_route(
                client, action, params, _ROUTES, service=SERVICE
            )
        except VaultwardenApiError as exc:
            return {"error": exc.message, "status": exc.status}
