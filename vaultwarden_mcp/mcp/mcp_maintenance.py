"""Vault maintenance and certified metadata-source MCP tools."""

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field
from scion_sdk.mcp.concurrency import run_blocking

from ..auth import get_client, get_vault_crypto
from ..vault.dedupe import DedupePlan, apply_plan, plan_deduplication
from ..vault.rotation import generate_password, rotate_item_password


async def _dedupe_plan(loose: bool, include_org: bool) -> DedupePlan:
    crypto = get_vault_crypto()
    items = await run_blocking(crypto.list_items, include_trash=False)
    return plan_deduplication(items, loose=loose, include_org=include_org)


async def _metadata_snapshot(
    client: Any, mode: str, checkpoint: str | None
) -> dict[str, Any]:
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
        mode=mode,
        checkpoint=checkpoint,
    )


def register_maintenance_tools(mcp: FastMCP):
    """Register the vault maintenance tools and the read-only metadata projection."""

    @mcp.tool(tags={"maintenance", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_maintenance_plan_deduplication(
        loose: bool = Field(default=False, description="Also group near-duplicates."),
        include_org: bool = Field(
            default=False, description="Include organization-owned items."
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Plan vault deduplication. The result carries item ids and counts only.

        CONCEPT:VW-ECO.mcp.maintenance-operations
        """
        plan = await _dedupe_plan(loose, include_org)
        return plan.summary()

    @mcp.tool(
        tags={"maintenance"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def vaultwarden_maintenance_apply_deduplication(
        include_org: bool = Field(
            default=False, description="Include organization-owned items."
        ),
        confirm: bool = Field(
            default=False, description="Must be true; set only after the person agrees."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Move the duplicate items of a strict plan to the trash.

        A loose plan is never applied automatically.

        CONCEPT:VW-ECO.mcp.maintenance-operations
        """
        if not confirm:
            return {
                "confirm_required": True,
                "message": "apply_deduplication requires confirm: true",
            }
        plan = await _dedupe_plan(False, include_org)
        trashed = await run_blocking(apply_plan, client, plan)
        return {"trashed": trashed, "duplicate_groups": len(plan.groups)}

    @mcp.tool(
        tags={"maintenance"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def vaultwarden_maintenance_rotate_password(
        item_id: str = Field(description="Id of the login item to rotate."),
        length: int = Field(default=24, description="Length of the new password."),
        use_symbols: bool = Field(default=True, description="Include symbols."),
        confirm: bool = Field(
            default=False, description="Must be true; set only after the person agrees."
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Replace a login item's password with a generated one; the old one goes to history.

        The new password is stored in the vault and never returned.

        CONCEPT:VW-ECO.mcp.maintenance-operations
        """
        if not confirm:
            return {
                "confirm_required": True,
                "message": "rotate_password requires confirm: true",
            }
        crypto = get_vault_crypto()
        return await run_blocking(
            rotate_item_password,
            crypto,
            item_id,
            length=length,
            use_symbols=use_symbols,
        )

    @mcp.tool(tags={"maintenance", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_maintenance_generate_password(
        length: int = Field(default=24, description="Length of the password."),
        use_symbols: bool = Field(default=True, description="Include symbols."),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Generate a random password locally without storing it.

        CONCEPT:VW-ECO.mcp.maintenance-operations
        """
        return {"password": generate_password(length, use_symbols)}

    @mcp.tool(tags={"metadata", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_metadata_snapshot(
        mode: str = Field(default="delta", description="'delta' or 'full'."),
        checkpoint: str | None = Field(
            default=None, description="Revision timestamp of the last snapshot."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Serve the certified metadata-only source projection.

        Returns opaque identifiers, type codes, lifecycle timestamps, counts and
        typed relationships; no names, notes, usernames, passwords or URIs.
        Scion SDK source_sync is the only graph commit, checkpoint and reconcile
        authority.

        CONCEPT:VW-KG.ingest.metadata-only
        """
        return await _metadata_snapshot(client, mode, checkpoint)

    @mcp.tool(tags={"metadata", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_metadata_backfeed(
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Refuse a backfeed: the metadata source is read-only.

        CONCEPT:VW-KG.ingest.metadata-only
        """
        from .. import kg_ingest

        kg_ingest.refuse_backfeed()
        raise AssertionError("unreachable")
