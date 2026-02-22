from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

from ticktick_mcp.client import TickTickClient
from ticktick_mcp.dates import date_to_epoch_ms


def _get_client(ctx: Context) -> TickTickClient:
    return ctx.request_context.lifespan_context["client"]  # type: ignore[union-attr]


def _generate_focus_id() -> str:
    """Generate a time-based hex ID for focus sessions."""
    ms = int(time.time() * 1000)
    seed = ms ^ 0xDEAD_BEEF_CAFE_BABE
    return f"{ms:x}{seed & 0xFFFFFFFF:08x}"


def _now_iso() -> str:
    """Current time in ISO format with +0000 UTC offset."""
    now = datetime.now(UTC)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}+0000"


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def focus_status(ctx: Context) -> Any:
        """Get the current focus/pomodoro timer status.

        Returns the active timer state including elapsed time, task association,
        and whether it's running or paused. Requires v2 session token.
        """
        client = _get_client(ctx)
        return await client.v2_get("/timer")

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def focus_stats(ctx: Context) -> Any:
        """Get focus/pomodoro statistics.

        Returns daily and total focus time statistics including session counts
        and total minutes. Requires v2 session token.
        """
        client = _get_client(ctx)
        return await client.v2_get("/pomodoros/statistics/generalForDesktop")

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def focus_log(
        ctx: Context,
        from_date: str,
        to_date: str,
    ) -> Any:
        """Get focus session log for a date range.

        Args:
            from_date: Start date: "today", "yesterday", or "YYYY-MM-DD".
            to_date: End date: "today", "yesterday", or "YYYY-MM-DD".
        """
        client = _get_client(ctx)
        from_ms = date_to_epoch_ms(from_date)
        to_ms = date_to_epoch_ms(to_date) + 86400000 - 1  # End of day
        return await client.v2_get(f"/pomodoros?from={from_ms}&to={to_ms}")

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    async def focus_timeline(ctx: Context) -> Any:
        """Get the full focus session timeline.

        Returns all focus sessions in chronological order.
        Requires v2 session token.
        """
        client = _get_client(ctx)
        return await client.v2_get("/pomodoros/timeline")

    @mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def focus_start(
        ctx: Context,
        duration_minutes: int = 25,
        task_id: str | None = None,
        project_id: str | None = None,
    ) -> Any:
        """Start a new focus/pomodoro session.

        Args:
            duration_minutes: Focus duration in minutes (default: 25).
            task_id: Optional task ID to associate with this focus session.
            project_id: Optional project ID (required if task_id is provided).
        """
        client = _get_client(ctx)
        session_id = _generate_focus_id()
        now = _now_iso()
        now_ms = int(time.time() * 1000)

        op: dict[str, Any] = {
            "op": "start",
            "id": session_id,
            "startTime": now,
            "estimatedPomo": duration_minutes * 60 * 1000,
            "opTime": now_ms,
        }

        if task_id:
            op["taskId"] = task_id
        if project_id:
            op["projectId"] = project_id

        return await client.focus_op([op])

    @mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def focus_control(
        ctx: Context,
        action: str,
        session_id: str | None = None,
    ) -> Any:
        """Control an active focus session (pause, resume, or stop).

        Use focus_status to get the current session ID if needed.

        Args:
            action: "pause", "resume", or "stop".
            session_id: The focus session ID. If omitted, fetches the current session.
        """
        client = _get_client(ctx)

        if action not in ("pause", "resume", "stop"):
            raise ToolError(f"Invalid action '{action}'. Use: pause, resume, stop")

        if not session_id:
            status = await client.v2_get("/timer")
            session_id = status.get("id") or status.get("focusId")
            if not session_id:
                raise ToolError("No active focus session found")

        now_ms = int(time.time() * 1000)
        op: dict[str, Any] = {
            "op": action,
            "id": session_id,
            "opTime": now_ms,
        }

        if action == "stop":
            op["endTime"] = _now_iso()

        return await client.focus_op([op])
