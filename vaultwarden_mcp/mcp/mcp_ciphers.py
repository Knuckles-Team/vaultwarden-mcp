"""Cipher (vault item) MCP tool: decrypted item CRUD plus every raw route."""

import json
from typing import Any

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client, get_vault_crypto
from ._dispatch import SERVICE, dispatch_route, domain_routes, parse_params

_ROUTES = domain_routes("ciphers")
_DECRYPTED_ACTIONS = {
    "list_items",
    "get_item",
    "create_item",
    "edit_item",
    "move_to_trash",
}
_ACTIONS = sorted(set(_ROUTES) | _DECRYPTED_ACTIONS)


async def _decrypted_action(action: str, params: dict[str, Any]) -> dict | None:
    """Handle the four decrypted item actions; ``None`` when ``action`` is not one."""
    if action == "list_items":
        crypto = get_vault_crypto()
        include_trash = bool(params.get("include_trash", False))
        items = await run_blocking(crypto.list_items, include_trash=include_trash)
        return {"items": items}
    if action == "get_item":
        item_id = params.get("item_id")
        if not item_id:
            return {"error": "get_item requires 'item_id'"}
        crypto = get_vault_crypto()
        return {"item": await run_blocking(crypto.get_item, item_id)}
    if action == "create_item":
        item = params.get("item")
        if not isinstance(item, dict):
            return {"error": "create_item requires an 'item' object"}
        crypto = get_vault_crypto()
        return {"item": await run_blocking(crypto.create_item, item)}
    if action == "edit_item":
        item_id = params.get("item_id")
        item = params.get("item")
        if not item_id or not isinstance(item, dict):
            return {"error": "edit_item requires 'item_id' and an 'item' object"}
        crypto = get_vault_crypto()
        return {"item": await run_blocking(crypto.edit_item, item_id, item)}
    return None


async def _move_to_trash(client: Any, params: dict[str, Any]) -> dict:
    ids = params.get("ids")
    if not isinstance(ids, list) or not ids:
        return {"error": "move_to_trash requires a non-empty 'ids' list"}
    result = await run_blocking(client.soft_delete_ciphers, ids)
    return {"trashed": len(ids), "result": result}


def register_ciphers_tools(mcp: FastMCP):
    """Register the cipher (vault item) tool."""

    @mcp.tool(tags={"ciphers"})
    async def vaultwarden_ciphers(
        action: str = Field(
            description=(
                "One of 'list_items', 'get_item', 'create_item', 'edit_item', "
                "'move_to_trash', or any raw ciphers-domain Route.name. Call "
                "with action='list_actions' to list every available operation."
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
        """Read and write vault items (ciphers).

        The decrypted actions (``list_items``, ``get_item``, ``create_item``,
        ``edit_item``) return or accept plaintext item contents because the
        caller explicitly asked for them — never log, echo, or otherwise
        surface that content elsewhere. ``move_to_trash`` soft-deletes items
        by id (recoverable). Every other ``ciphers`` API route is reachable
        by its route name via ``call_operation``.

        CONCEPT:VW-ECO.mcp.cipher-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_ciphers action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}

        resolved = resolve_action(action, _ACTIONS, service=SERVICE)
        if isinstance(resolved, dict):
            return resolved
        if resolved == "move_to_trash":
            return await _move_to_trash(client, params)
        decrypted = await _decrypted_action(resolved, params)
        if decrypted is not None:
            return decrypted
        return await dispatch_route(client, resolved, params, _ROUTES, service=SERVICE)
