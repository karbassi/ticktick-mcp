from __future__ import annotations

import json

from fastmcp import Context, FastMCP

from ticktick_mcp.client import TickTickClient


def _get_client(ctx: Context) -> TickTickClient:
    return ctx.request_context.lifespan_context["client"]  # type: ignore[union-attr]


def register(mcp: FastMCP) -> None:
    @mcp.resource("ticktick://profile")
    async def profile(ctx: Context) -> str:
        """User profile and subscription status merged into one view."""
        client = _get_client(ctx)
        user_profile = await client.v2_get("/user/profile")
        user_status = await client.v2_get("/user/status")
        return json.dumps({**user_profile, "status": user_status})
