from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.client import V2_BASE, TickTickClient


class TestListCalendars:
    @pytest.mark.anyio
    async def test_list(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/calendar/third/accounts").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "cal1", "type": "google", "name": "Google Calendar"},
                    {"id": "cal2", "type": "outlook", "name": "Outlook"},
                ],
            )
        )
        result = await client.v2_get("/calendar/third/accounts")
        assert len(result) == 2
        assert result[0]["type"] == "google"


class TestListEvents:
    @pytest.mark.anyio
    async def test_list_events(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.post(f"{V2_BASE}/calendar/bind/events/all").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "ev1",
                        "title": "Standup",
                        "startDate": "2026-02-22T09:00:00.000+0000",
                        "endDate": "2026-02-22T09:30:00.000+0000",
                    }
                ],
            )
        )
        result = await client.v2_post(
            "/calendar/bind/events/all",
            {
                "begin": "2026-02-22T00:00:00.000+0000",
                "end": "2026-02-22T23:59:59.999+0000",
            },
        )
        assert len(result) == 1
        assert result[0]["title"] == "Standup"


class TestSyncAccount:
    @pytest.mark.anyio
    async def test_sync(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/batch/check/0").mock(
            return_value=httpx.Response(
                200,
                json={
                    "projectProfiles": [{"id": "p1", "name": "Work"}],
                    "tags": [{"name": "urgent"}],
                    "filters": [],
                    "projectGroups": [],
                },
            )
        )
        data = await client.batch_check()
        assert "projectProfiles" in data
        assert "tags" in data
