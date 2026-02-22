from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.client import V2_BASE, TickTickClient

HABITS_RESPONSE = [
    {"id": "h1", "name": "Exercise", "etag": "e1", "type": "Boolean", "goal": 1, "status": 0},
    {"id": "h2", "name": "Read", "etag": "e2", "type": "Numeric", "goal": 30, "unit": "pages"},
]

SECTIONS_RESPONSE = [
    {"id": "s1", "name": "Morning", "sortOrder": 0},
    {"id": "s2", "name": "Evening", "sortOrder": 1},
]


class TestListHabits:
    @pytest.mark.anyio
    async def test_list(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/habits").mock(
            return_value=httpx.Response(200, json=HABITS_RESPONSE)
        )
        result = await client.v2_get("/habits")
        assert len(result) == 2
        assert result[0]["name"] == "Exercise"


class TestAddHabit:
    @pytest.mark.anyio
    async def test_add_boolean(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habits/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"h_new": "etag_new"}})
        )
        result = await client.v2_post(
            "/habits/batch", {"add": [{"name": "Meditate", "type": "Boolean"}]}
        )
        assert "id2etag" in result

    @pytest.mark.anyio
    async def test_add_numeric(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habits/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"h_new": "etag_new"}})
        )
        result = await client.v2_post(
            "/habits/batch",
            {"add": [{"name": "Water", "type": "Numeric", "goal": 8, "unit": "glasses"}]},
        )
        assert "id2etag" in result


class TestEditHabit:
    @pytest.mark.anyio
    async def test_edit(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habits/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"h1": "e1_new"}})
        )
        result = await client.v2_post(
            "/habits/batch",
            {"update": [{"id": "h1", "etag": "e1", "name": "Workout"}]},
        )
        assert "id2etag" in result


class TestDeleteHabits:
    @pytest.mark.anyio
    async def test_delete(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habits/batch").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await client.v2_post("/habits/batch", {"delete": ["h1"]})
        assert result["ok"] is True


class TestCheckinHabit:
    @pytest.mark.anyio
    async def test_checkin(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habitCheckins/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"c1": "ce1"}})
        )
        result = await client.v2_post(
            "/habitCheckins/batch",
            {"add": [{"habitId": "h1", "checkinStamp": 20260222, "value": 1, "status": 0}]},
        )
        assert "id2etag" in result


class TestHabitLog:
    @pytest.mark.anyio
    async def test_query(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habitCheckins/query").mock(
            return_value=httpx.Response(200, json={"checkins": [{"habitId": "h1", "value": 1}]})
        )
        result = await client.v2_post(
            "/habitCheckins/query",
            {"habitIds": ["h1"], "afterStamp": 20260201},
        )
        assert "checkins" in result


class TestArchiveHabits:
    @pytest.mark.anyio
    async def test_archive(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habits/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"h1": "e1_arch"}})
        )
        result = await client.v2_post(
            "/habits/batch", {"update": [{"id": "h1", "etag": "e1", "status": 1}]}
        )
        assert "id2etag" in result


class TestManageSections:
    @pytest.mark.anyio
    async def test_list_sections(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/habitSections").mock(
            return_value=httpx.Response(200, json=SECTIONS_RESPONSE)
        )
        result = await client.v2_get("/habitSections")
        assert len(result) == 2

    @pytest.mark.anyio
    async def test_add_section(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habitSections/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"s_new": "se_new"}})
        )
        result = await client.v2_post("/habitSections/batch", {"add": [{"name": "Afternoon"}]})
        assert "id2etag" in result

    @pytest.mark.anyio
    async def test_delete_section(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habitSections/batch").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await client.v2_post("/habitSections/batch", {"delete": ["s1"]})
        assert result["ok"] is True

    @pytest.mark.anyio
    async def test_rename_section(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/habitSections/batch").mock(
            return_value=httpx.Response(200, json={"id2etag": {"s1": "se_new"}})
        )
        result = await client.v2_post(
            "/habitSections/batch",
            {"update": [{"id": "s1", "name": "Early Morning"}]},
        )
        assert "id2etag" in result
