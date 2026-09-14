"""Bitwarden Send MCP tool."""

import json

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client
from ._dispatch import SERVICE, dispatch_route, domain_routes, parse_params

_ROUTES = domain_routes("sends")


def register_sends_tools(mcp: FastMCP):
    """Register the Bitwarden Send tool."""

    @mcp.tool(tags={"sends"})
    async def vaultwarden_sends(
        action: str = Field(
            description=(
                "Vaultwarden sends operation name (a Route.name). Call with "
                "action='list_actions' to list every available operation."
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
        """Create, list, update, and remove Bitwarden Sends (text or file).

        Dispatches to every Vaultwarden ``sends`` API route by its route
        name.

        CONCEPT:VW-ECO.mcp.send-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_sends action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}
        return await dispatch_route(client, action, params, _ROUTES, service=SERVICE)
