from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from ticktick_mcp.client import TickTickClient


def _get_client(ctx: Context) -> TickTickClient:
    return ctx.request_context.lifespan_context["client"]  # type: ignore[union-attr]


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def list_calendars(ctx: Context) -> Any:
        """List third-party calendar accounts connected to TickTick.

        Returns connected calendar accounts (Google Calendar, Outlook, etc.)
        with their sync status. Requires v2 session token.
        """
        client = _get_client(ctx)
        return await client.v2_get("/calendar/third/accounts")

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def list_events(
        ctx: Context,
        begin: str,
        end: str,
    ) -> Any:
        """Query calendar events for a date range.

        Returns events from all connected calendars within the specified date range.

        Args:
            begin: Start datetime in ISO format (e.g. "2026-02-11T00:00:00.000+0000").
            end: End datetime in ISO format (e.g. "2026-02-18T23:59:59.999+0000").
        """
        client = _get_client(ctx)
        return await client.v2_post(
            "/calendar/bind/events/all",
            {"begin": begin, "end": end},
        )

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def sync_account(ctx: Context) -> dict[str, Any]:
        """Perform a full account sync.

        Fetches the complete account state including all projects, tasks, tags,
        filters, folders, and settings. Useful for getting a comprehensive view
        of the account or forcing a refresh. Requires v2 session token.
        """
        client = _get_client(ctx)
        return await client.batch_check()
