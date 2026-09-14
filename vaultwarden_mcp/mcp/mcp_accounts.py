"""Account, two-factor, emergency-access, and event-feed MCP tool."""

import json

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client
from ._dispatch import SERVICE, dispatch_route, domain_routes, parse_params

_ROUTES = domain_routes("accounts", "two_factor", "emergency_access", "events")


def register_accounts_tools(mcp: FastMCP):
    """Register the account/two-factor/emergency-access/events tool."""

    @mcp.tool(tags={"accounts"})
    async def vaultwarden_accounts(
        action: str = Field(
            description=(
                "Vaultwarden accounts/two_factor/emergency_access/events "
                "operation name (a Route.name). Call with action='list_actions' "
                "to list every available operation."
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
        """Operate the account profile, two-factor methods, emergency access,
        and audit event feeds.

        Dispatches to every Vaultwarden ``accounts``, ``two_factor``,
        ``emergency_access``, and ``events`` API route by its route name.

        CONCEPT:VW-ECO.mcp.account-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_accounts action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}
        return await dispatch_route(client, action, params, _ROUTES, service=SERVICE)
