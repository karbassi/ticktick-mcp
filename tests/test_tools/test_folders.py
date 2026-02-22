from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.client import V2_BASE, TickTickClient

BATCH_CHECK_RESPONSE = {
    "projectGroups": [
        {"id": "g1", "name": "Home", "etag": "e1", "sortOrder": 0},
        {"id": "g2", "name": "Work", "etag": "e2", "sortOrder": 1},
    ],
    "filters": [],
}


class TestListFolders:
    @pytest.mark.anyio
    async def test_list(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/batch/check/0").mock(
            return_value=httpx.Response(200, json=BATCH_CHECK_RESPONSE)
        )
        data = await client.batch_check()
        groups = data.get("projectGroups", [])
        assert len(groups) == 2
        assert groups[0]["name"] == "Home"


class TestAddFolder:
    @pytest.mark.anyio
    async def test_add(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/projectGroup").mock(
            return_value=httpx.Response(200, json={"id2etag": {"g_new": "etag_new"}})
        )
        result = await client.v2_post(
            "/batch/projectGroup",
            {"add": [{"name": "Errands", "listType": "group"}]},
        )
        assert "id2etag" in result


class TestDeleteFolders:
    @pytest.mark.anyio
    async def test_delete(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/projectGroup").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await client.v2_post("/batch/projectGroup", {"delete": ["g1"]})
        assert result["ok"] is True


class TestRenameFolder:
    @pytest.mark.anyio
    async def test_rename(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/projectGroup").mock(
            return_value=httpx.Response(200, json={"id2etag": {"g1": "etag_new"}})
        )
        result = await client.v2_post(
            "/batch/projectGroup",
            {"update": [{"id": "g1", "etag": "e1", "name": "Renamed", "listType": "group"}]},
        )
        assert "id2etag" in result
