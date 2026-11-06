"""Folder MCP tools: decrypted folder reads and writes, one tool per operation."""

from fastmcp import Context, FastMCP
from pydantic import Field
from scion_sdk.mcp.concurrency import run_blocking

from ..auth import get_vault_crypto


def register_folders_tools(mcp: FastMCP):
    """Register the personal-vault folder tools."""

    @mcp.tool(tags={"folders", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_folders_list_folders(
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """List personal-vault folders with their decrypted names.

        CONCEPT:VW-ECO.mcp.folder-operations
        """
        crypto = get_vault_crypto()
        return {"folders": await run_blocking(crypto.list_folders)}

    @mcp.tool(
        tags={"folders"}, annotations={"readOnlyHint": False, "destructiveHint": False}
    )
    async def vaultwarden_folders_create_folder(
        name: str = Field(description="Name of the new folder."),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Create a personal-vault folder; the name is stored encrypted.

        CONCEPT:VW-ECO.mcp.folder-operations
        """
        crypto = get_vault_crypto()
        return {"folder": await run_blocking(crypto.create_folder, name)}
