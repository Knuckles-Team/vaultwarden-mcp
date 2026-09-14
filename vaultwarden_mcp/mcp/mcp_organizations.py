"""Organization, collection, member, group, policy, public, and misc MCP tool."""

import json

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client
from ._dispatch import SERVICE, dispatch_route, domain_routes, parse_params

_ROUTES = domain_routes("organizations", "public", "misc")


def register_organizations_tools(mcp: FastMCP):
    """Register the organizations/public/misc tool."""

    @mcp.tool(tags={"organizations"})
    async def vaultwarden_organizations(
        action: str = Field(
            description=(
                "Vaultwarden organizations/public/misc operation name (a "
                "Route.name). Call with action='list_actions' to list every "
                "available operation."
            )
        ),
        params_json: str = Field(
            default="{}",
            description="JSON object of path/query parameters for the action.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Manage organizations, collections, members, groups, and policies,
        plus the public LDAP import and misc server-settings/HIBP routes.

        Dispatches to every Vaultwarden ``organizations``, ``public``, and
        ``misc`` API route by its route name.

        CONCEPT:VW-ECO.mcp.organization-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_organizations action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}
        return await dispatch_route(client, action, params, _ROUTES, service=SERVICE)
