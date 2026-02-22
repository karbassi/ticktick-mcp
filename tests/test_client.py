from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.client import (
    V1_BASE,
    V2_BASE,
    TickTickClient,
    generate_device_id,
    url_encode,
    x_device_header,
)


class TestDeviceId:
    def test_format(self):
        device_id = generate_device_id()
        assert len(device_id) == 24
        assert device_id.startswith("6490")
        assert all(c in "0123456789abcdef" for c in device_id[4:])

    def test_uniqueness(self):
        id1 = generate_device_id()
        id2 = generate_device_id()
        assert id1 != id2


class TestXDeviceHeader:
    def test_valid_json(self):
        import json

        header = x_device_header("6490abcdef1234567890")
        parsed = json.loads(header)
        assert parsed["id"] == "6490abcdef1234567890"
        assert parsed["platform"] == "web"
        assert parsed["version"] == 6490


class TestUrlEncode:
    def test_spaces(self):
        assert url_encode("hello world") == "hello%20world"

    def test_special_chars(self):
        assert url_encode("a+b") == "a%2Bb"

    def test_preserves_unreserved(self):
        assert url_encode("abc-123_def.ghi~") == "abc-123_def.ghi~"


class TestV1Auth:
    @pytest.mark.anyio
    async def test_get_success(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V1_BASE}/project").mock(
            return_value=httpx.Response(200, json=[{"id": "p1", "name": "Test"}])
        )
        result = await client.v1_get("/project")
        assert result == [{"id": "p1", "name": "Test"}]

    @pytest.mark.anyio
    async def test_401_refresh_retry(self, client: TickTickClient, mock_api: respx.MockRouter):
        # First call returns 401, refresh succeeds, retry succeeds
        mock_api.get(f"{V1_BASE}/project").mock(
            side_effect=[
                httpx.Response(401, json={"error": "unauthorized"}),
                httpx.Response(200, json=[{"id": "p1"}]),
            ]
        )
        mock_api.post("https://ticktick.com/oauth/token").mock(
            return_value=httpx.Response(
                200, json={"access_token": "new-token", "refresh_token": "new-refresh"}
            )
        )
        result = await client.v1_get("/project")
        assert result == [{"id": "p1"}]
        assert client._access_token == "new-token"

    @pytest.mark.anyio
    async def test_post_json(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V1_BASE}/task").mock(
            return_value=httpx.Response(200, json={"id": "t1", "title": "Test"})
        )
        result = await client.v1_post("/task", {"title": "Test"})
        assert result["id"] == "t1"

    @pytest.mark.anyio
    async def test_delete(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.delete(f"{V1_BASE}/project/p1/task/t1").mock(return_value=httpx.Response(200))
        resp = await client.v1_delete("/project/p1/task/t1")
        assert resp.status_code == 200


class TestV2Auth:
    @pytest.mark.anyio
    async def test_get_with_session(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/tags").mock(
            return_value=httpx.Response(200, json=[{"name": "work"}])
        )
        result = await client.v2_get("/tags")
        assert result == [{"name": "work"}]

    @pytest.mark.anyio
    async def test_post(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/tag").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await client.v2_post("/batch/tag", {"add": [{"name": "test"}]})
        assert result["ok"] is True

    @pytest.mark.anyio
    async def test_requires_session_token(self):
        c = TickTickClient(access_token="tok")
        async with c:
            with pytest.raises(RuntimeError, match="session token"):
                await c.v2_get("/tags")
