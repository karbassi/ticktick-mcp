from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from ticktick_mcp.client import TickTickClient


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    client = TickTickClient(
        access_token=os.environ["TICKTICK_ACCESS_TOKEN"],
        client_id=os.environ.get("TICKTICK_CLIENT_ID"),
        client_secret=os.environ.get("TICKTICK_CLIENT_SECRET"),
        session_token=os.environ.get("TICKTICK_V2_SESSION_TOKEN"),
        refresh_token=os.environ.get("TICKTICK_REFRESH_TOKEN"),
    )
    async with client:
        yield {"client": client}


mcp = FastMCP("TickTick", lifespan=lifespan)

# Register tool and resource modules
from ticktick_mcp.resources import register_resources  # noqa: E402
from ticktick_mcp.tools import register_tools  # noqa: E402

register_tools(mcp)
register_resources(mcp)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
