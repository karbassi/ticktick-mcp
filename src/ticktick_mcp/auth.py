from __future__ import annotations

import base64
from typing import Any

import httpx

TOKEN_URL = "https://ticktick.com/oauth/token"


async def refresh_access_token(
    http: httpx.AsyncClient,
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> tuple[str, str | None]:
    """Exchange a refresh token for a new access token.

    Returns (new_access_token, optional_new_refresh_token).
    """
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    resp = await http.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        content=f"grant_type=refresh_token&refresh_token={refresh_token}",
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    return data["access_token"], data.get("refresh_token")
