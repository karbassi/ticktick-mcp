from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from ticktick_mcp.client import TickTickClient


def _get_client(ctx: Context) -> TickTickClient:
    return ctx.request_context.lifespan_context["client"]  # type: ignore[union-attr]


def register(mcp: FastMCP) -> None:
    @mcp.resource("ticktick://settings")
    async def settings(ctx: Context) -> dict[str, Any]:
        """User preference settings including web-specific options."""
        client = _get_client(ctx)
        return await client.v2_get("/user/preferences/settings?includeWeb=true")
