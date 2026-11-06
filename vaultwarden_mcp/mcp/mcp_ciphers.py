"""Cipher (vault item) MCP tools: decrypted item reads and writes, one tool per operation."""

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field
from scion_sdk.mcp.concurrency import run_blocking

from ..auth import get_client, get_vault_crypto


def register_ciphers_tools(mcp: FastMCP):
    """Register the decrypted cipher (vault item) tools."""

    @mcp.tool(tags={"ciphers", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_ciphers_list_items(
        include_trash: bool = Field(
            default=False, description="Include items that are in the trash."
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """List every vault item with its decrypted contents.

        The caller explicitly asked for plaintext, so never log, echo or surface
        the result anywhere else.

        CONCEPT:VW-ECO.mcp.cipher-operations
        """
        crypto = get_vault_crypto()
        items = await run_blocking(crypto.list_items, include_trash=include_trash)
        return {"items": items}

    @mcp.tool(tags={"ciphers", "read-only"}, annotations={"readOnlyHint": True})
    async def vaultwarden_ciphers_get_item(
        item_id: str = Field(description="Id of the vault item."),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Read one vault item with its decrypted contents.

        CONCEPT:VW-ECO.mcp.cipher-operations
        """
        crypto = get_vault_crypto()
        return {"item": await run_blocking(crypto.get_item, item_id)}

    @mcp.tool(
        tags={"ciphers"}, annotations={"readOnlyHint": False, "destructiveHint": False}
    )
    async def vaultwarden_ciphers_create_item(
        item: dict[str, Any] = Field(
            description="The vault item: type, name and the type-specific fields."
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Create a vault item from plaintext fields; the server stores it encrypted.

        CONCEPT:VW-ECO.mcp.cipher-operations
        """
        crypto = get_vault_crypto()
        return {"item": await run_blocking(crypto.create_item, item)}

    @mcp.tool(
        tags={"ciphers"}, annotations={"readOnlyHint": False, "destructiveHint": False}
    )
    async def vaultwarden_ciphers_edit_item(
        item_id: str = Field(description="Id of the vault item to change."),
        item: dict[str, Any] = Field(description="The fields to change."),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Change fields of a vault item; the previous password goes to its history.

        CONCEPT:VW-ECO.mcp.cipher-operations
        """
        crypto = get_vault_crypto()
        return {"item": await run_blocking(crypto.edit_item, item_id, item)}

    @mcp.tool(
        tags={"ciphers"}, annotations={"readOnlyHint": False, "destructiveHint": False}
    )
    async def vaultwarden_ciphers_move_to_trash(
        ids: list[str] = Field(min_length=1, description="Ids of the items to trash."),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Move items to the trash. Recoverable until the trash is purged.

        CONCEPT:VW-ECO.mcp.cipher-operations
        """
        result = await run_blocking(client.soft_delete_ciphers, ids)
        return {"trashed": len(ids), "result": result}
