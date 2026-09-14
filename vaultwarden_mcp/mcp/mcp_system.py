import json

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client
from ._dispatch import SERVICE

_ACTIONS = {"alive", "version", "config"}


def register_system_tools(mcp: FastMCP):
    """Register server status tools."""

    @mcp.tool(tags={"system"})
    async def vaultwarden_system(
        action: str = Field(
            description="Action to perform. One of: 'alive', 'version', 'config'."
        ),
        params_json: str = Field(
            default="{}", description="JSON object of parameters (none required)."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Read Vaultwarden server liveness, version, and public configuration.

        CONCEPT:VW-ECO.mcp.system-operations
        """
        if ctx:
            await ctx.info("Reading Vaultwarden server status...")
        try:
            json.loads(params_json)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid params_json: {type(e).__name__}"}

        resolved = resolve_action(action, _ACTIONS, service=SERVICE)
        if isinstance(resolved, dict):
            return resolved
        if resolved == "alive":
            return {"alive": await run_blocking(client.server_alive)}
        if resolved == "version":
            return {"version": await run_blocking(client.server_version)}
        return {"config": await run_blocking(client.server_config)}
