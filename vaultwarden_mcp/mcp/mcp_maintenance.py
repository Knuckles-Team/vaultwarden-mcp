"""Vault maintenance and certified metadata-source MCP tools."""

import json
from typing import Any, Literal

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client, get_vault_crypto
from ..vault.dedupe import DedupePlan, apply_plan, plan_deduplication
from ..vault.rotation import generate_password, rotate_item_password
from ._dispatch import SERVICE, parse_params

_MAINTENANCE_ACTIONS = {
    "plan_deduplication",
    "apply_deduplication",
    "rotate_password",
    "generate_password",
}
_METADATA_ACTIONS = {"metadata_snapshot", "backfeed_metadata"}


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


async def _metadata_snapshot(client: Any, params: dict[str, Any]) -> dict[str, Any]:
    """Fetch once and project only the certified structural metadata."""
    from .. import kg_ingest

    sync = await run_blocking(client.sync_vault)
    if not isinstance(sync, dict):
        raise ValueError("Vaultwarden sync returned a malformed response")
    config = await run_blocking(client.server_config)
    version = await run_blocking(client.server_version) if config else None
    return kg_ingest.build_metadata_snapshot(
        items=sync.get("ciphers") or [],
        folders=sync.get("folders") or [],
        collections=sync.get("collections") or [],
        config=config,
        server_version=version,
        mode=str(params.get("mode") or "delta"),
        checkpoint=params.get("checkpoint"),
    )


def register_maintenance_tools(mcp: FastMCP):
    """Register disjoint mutation and read-only metadata tools."""

    @mcp.tool(tags={"maintenance"})
    async def vaultwarden_maintenance(
        action: str = Field(
            description=(
                "One of 'plan_deduplication', 'apply_deduplication', "
                "'rotate_password', or 'generate_password'."
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
        """Plan/apply vault deduplication and rotate or generate passwords.

        Deduplication and rotation results carry item ids and counts only.
        Applying deduplication or rotating a password requires confirm: true,
        and a loose deduplication plan is never applied automatically.

        CONCEPT:VW-ECO.mcp.maintenance-operations
        """
        if ctx:
            await ctx.info(f"vaultwarden_maintenance action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}

        resolved = resolve_action(action, _MAINTENANCE_ACTIONS, service=SERVICE)
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
        raise AssertionError("unreachable")

    @mcp.tool(
        tags={"metadata", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        meta={
            "eg.annotations": {"modalities_in": ["text"], "modalities_out": ["text"]}
        },
    )
    async def vaultwarden_metadata(
        action: Literal["backfeed_metadata", "metadata_snapshot"] = Field(
            description="One of 'metadata_snapshot' or 'backfeed_metadata'."
        ),
        params_json: str = Field(
            default="{}", description="JSON object of metadata-source parameters."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Serve the certified metadata-only source projection.

        metadata_snapshot returns opaque identifiers, type codes, lifecycle
        timestamps, counts, and typed relationships. Agent Utilities source_sync
        is the only graph commit/checkpoint/reconcile authority. Backfeed is
        explicitly unsupported.

        CONCEPT:VW-KG.ingest.metadata-only
        """
        if ctx:
            await ctx.info(f"vaultwarden_metadata action={action}")
        try:
            params = parse_params(params_json)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": f"Invalid params_json: {type(exc).__name__}"}

        resolved = resolve_action(action, _METADATA_ACTIONS, service=SERVICE)
        if isinstance(resolved, dict):
            return resolved
        if resolved == "metadata_snapshot":
            return await _metadata_snapshot(client, params)
        from .. import kg_ingest

        kg_ingest.refuse_backfeed()
        raise AssertionError("unreachable")
