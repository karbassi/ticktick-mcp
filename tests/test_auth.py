from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.auth import TOKEN_URL, refresh_access_token


class TestRefreshToken:
    @pytest.mark.anyio
    async def test_refresh_success(self, mock_api: respx.MockRouter):
        mock_api.post(TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "new-access", "refresh_token": "new-refresh"},
            )
        )
        async with httpx.AsyncClient() as http:
            access, refresh = await refresh_access_token(
                http, "old-refresh", "client-id", "client-secret"
            )
        assert access == "new-access"
        assert refresh == "new-refresh"

    @pytest.mark.anyio
    async def test_refresh_no_new_refresh(self, mock_api: respx.MockRouter):
        mock_api.post(TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "new-access"},
            )
        )
        async with httpx.AsyncClient() as http:
            access, refresh = await refresh_access_token(
                http, "old-refresh", "client-id", "client-secret"
            )
        assert access == "new-access"
        assert refresh is None

    @pytest.mark.anyio
    async def test_refresh_failure(self, mock_api: respx.MockRouter):
        mock_api.post(TOKEN_URL).mock(
            return_value=httpx.Response(401, json={"error": "invalid_grant"})
        )
        async with httpx.AsyncClient() as http:
            with pytest.raises(httpx.HTTPStatusError):
                await refresh_access_token(http, "bad-refresh", "client-id", "client-secret")
