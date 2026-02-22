from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.client import V2_BASE, TickTickClient

BATCH_CHECK_RESPONSE = {
    "filters": [
        {"id": "f1", "name": "High Priority", "etag": "e1", "rule": '{"and":[],"type":0}'},
        {"id": "f2", "name": "Due Today", "etag": "e2"},
    ],
    "projectGroups": [],
}


class TestListFilters:
    @pytest.mark.anyio
    async def test_list(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/batch/check/0").mock(
            return_value=httpx.Response(200, json=BATCH_CHECK_RESPONSE)
        )
        data = await client.batch_check()
        filters = data.get("filters", [])
        assert len(filters) == 2
        assert filters[0]["name"] == "High Priority"


class TestAddFilter:
    @pytest.mark.anyio
    async def test_add(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/filter").mock(
            return_value=httpx.Response(200, json={"id2etag": {"f_new": "etag_new"}})
        )
        result = await client.v2_post(
            "/batch/filter",
            {"add": [{"name": "Overdue", "rule": '{"and":[],"type":1}'}]},
        )
        assert "id2etag" in result


class TestEditFilter:
    @pytest.mark.anyio
    async def test_edit(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/filter").mock(
            return_value=httpx.Response(200, json={"id2etag": {"f1": "e1_new"}})
        )
        result = await client.v2_post(
            "/batch/filter",
            {"update": [{"id": "f1", "etag": "e1", "name": "Very High Priority"}]},
        )
        assert "id2etag" in result


class TestDeleteFilters:
    @pytest.mark.anyio
    async def test_delete(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/batch/filter").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await client.v2_post("/batch/filter", {"delete": ["f1"]})
        assert result["ok"] is True
