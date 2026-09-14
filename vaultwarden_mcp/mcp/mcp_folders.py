"""Folder MCP tool: decrypted folder CRUD plus every raw route."""

import json

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client, get_vault_crypto
from ._dispatch import SERVICE, dispatch_route, domain_routes, parse_params

_ROUTES = domain_routes("folders")
_DECRYPTED_ACTIONS = {"list_folders", "create_folder"}
_ACTIONS = sorted(set(_ROUTES) | _DECRYPTED_ACTIONS)


def register_folders_tools(mcp: FastMCP):
    """Register the personal-vault folder tool."""

    @mcp.tool(tags={"folders"})
    async def vaultwarden_folders(
        action: str = Field(
            description=(
                "One of 'list_folders', 'create_folder', or any raw "
                "folders-domain Route.name. Call with action='list_actions' "
                "to list every available operation."
            )
        ),
        params_json: str = Field(
            default="{}", description="JSON object of parameters for the action."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Read and write personal-vault folders.

        ``list_folders`` and ``create_folder`` (``name``) return decrypted
        folder names because the caller explicitly asked for them. Every
        other ``folders`` API route is reachable by its route name via
        ``call_operation``.

        CONCEPT:VW-ECO.mcp.folder-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_folders action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}

        resolved = resolve_action(action, _ACTIONS, service=SERVICE)
        if isinstance(resolved, dict):
            return resolved
        if resolved == "list_folders":
            crypto = get_vault_crypto()
            return {"folders": await run_blocking(crypto.list_folders)}
        if resolved == "create_folder":
            name = params.get("name")
            if not name:
                return {"error": "create_folder requires 'name'"}
            crypto = get_vault_crypto()
            return {"folder": await run_blocking(crypto.create_folder, name)}
        return await dispatch_route(client, resolved, params, _ROUTES, service=SERVICE)
