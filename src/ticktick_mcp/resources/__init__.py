from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    from ticktick_mcp.resources import lists, profile, settings

    profile.register(mcp)
    settings.register(mcp)
    lists.register(mcp)
