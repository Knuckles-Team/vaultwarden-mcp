"""Vault maintenance MCP tool: deduplication, password rotation, KG ingestion."""

import json
from typing import Any

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client, get_vault_crypto
from ..vault.dedupe import DedupePlan, apply_plan, plan_deduplication
from ..vault.rotation import generate_password, rotate_item_password
from ._dispatch import SERVICE, parse_params

_ACTIONS = {
    "plan_deduplication",
    "apply_deduplication",
    "rotate_password",
    "generate_password",
    "ingest_metadata",
}


async def _dedupe_plan(params: dict[str, Any]) -> DedupePlan:
    crypto = get_vault_crypto()
    items = await run_blocking(crypto.list_items, include_trash=False)
    return plan_deduplication(
        items,
        loose=bool(params.get("loose", False)),
        include_org=bool(params.get("include_org", False)),
    )


async def _apply_deduplication(client: Any, params: dict[str, Any]) -> dict:
    if not params.get("confirm"):
        return {
            "confirm_required": True,
            "message": "apply_deduplication requires confirm: true",
        }
    plan = await _dedupe_plan(params)
    if plan.loose:
        return {"error": "a loose plan cannot be applied automatically; review it"}
    trashed = await run_blocking(apply_plan, client, plan)
    return {"trashed": trashed, "duplicate_groups": len(plan.groups)}


async def _rotate_password(params: dict[str, Any]) -> dict:
    item_id = params.get("item_id")
    if not item_id:
        return {"error": "rotate_password requires 'item_id'"}
    if not params.get("confirm"):
        return {
            "confirm_required": True,
            "message": "rotate_password requires confirm: true",
        }
    crypto = get_vault_crypto()
    length = int(params.get("length", 24))
    use_symbols = bool(params.get("use_symbols", True))
    return await run_blocking(
        rotate_item_password, crypto, item_id, length=length, use_symbols=use_symbols
    )


async def _ingest_metadata(client: Any) -> dict:
    from .. import kg_ingest

    sync = await run_blocking(client.sync_vault)
    counts: dict[str, int] = {}

    ciphers = sync.get("ciphers") or []
    if ciphers:
        result = await run_blocking(kg_ingest.ingest_items, ciphers)
        counts["items"] = sum(result.values())

    folder_ids = [f.get("id") for f in sync.get("folders") or [] if f.get("id")]
    if folder_ids:
        result = await run_blocking(kg_ingest.ingest_folders, folder_ids)
        counts["folders"] = sum(result.values())

    collections = sync.get("collections") or []
    if collections:
        result = await run_blocking(kg_ingest.ingest_collections, collections)
        counts["collections"] = sum(result.values())

    config = await run_blocking(client.server_config)
    if config:
        version = await run_blocking(client.server_version)
        result = await run_blocking(
            kg_ingest.ingest_server, config, server_version=version
        )
        counts["server"] = sum(result.values())

    return {"synced": True, "counts": counts}


def register_maintenance_tools(mcp: FastMCP):
    """Register the vault-maintenance tool."""

    @mcp.tool(tags={"maintenance"})
    async def vaultwarden_maintenance(
        action: str = Field(
            description=(
                "One of 'plan_deduplication', 'apply_deduplication', "
                "'rotate_password', 'generate_password', 'ingest_metadata'."
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
        """Plan/apply vault deduplication, rotate item passwords, generate
        passwords, and sync vault metadata into the knowledge graph.

        Deduplication and rotation results carry item ids and counts only —
        never item names, usernames, or passwords. ``apply_deduplication``
        and ``rotate_password`` both require ``confirm: true``; a loose
        deduplication plan is always refused for ``apply_deduplication``.

        CONCEPT:VW-ECO.mcp.maintenance-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_maintenance action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}

        resolved = resolve_action(action, _ACTIONS, service=SERVICE)
        if isinstance(resolved, dict):
            return resolved
        if resolved == "plan_deduplication":
            plan = await _dedupe_plan(params)
            return plan.summary()
        if resolved == "apply_deduplication":
            return await _apply_deduplication(client, params)
        if resolved == "rotate_password":
            return await _rotate_password(params)
        if resolved == "generate_password":
            length = int(params.get("length", 24))
            use_symbols = bool(params.get("use_symbols", True))
            return {"password": generate_password(length, use_symbols)}
        return await _ingest_metadata(client)
