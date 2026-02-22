from __future__ import annotations

import httpx
import pytest
import respx

from ticktick_mcp.client import V2_BASE, TickTickClient


class TestFocusStatus:
    @pytest.mark.anyio
    async def test_status(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/timer").mock(
            return_value=httpx.Response(
                200, json={"id": "fs1", "status": "running", "elapsed": 600000}
            )
        )
        result = await client.v2_get("/timer")
        assert result["id"] == "fs1"
        assert result["status"] == "running"


class TestFocusStats:
    @pytest.mark.anyio
    async def test_stats(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/pomodoros/statistics/generalForDesktop").mock(
            return_value=httpx.Response(200, json={"todayFocus": 3600000, "totalSessions": 42})
        )
        result = await client.v2_get("/pomodoros/statistics/generalForDesktop")
        assert result["totalSessions"] == 42


class TestFocusLog:
    @pytest.mark.anyio
    async def test_log(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(url__regex=r".*/pomodoros\?from=\d+&to=\d+").mock(
            return_value=httpx.Response(200, json=[{"id": "p1", "duration": 1500000}])
        )
        result = await client.v2_get("/pomodoros?from=1740182400000&to=1740268799999")
        assert len(result) == 1
        assert result[0]["duration"] == 1500000


class TestFocusTimeline:
    @pytest.mark.anyio
    async def test_timeline(self, client: TickTickClient, mock_api: respx.MockRouter):
        mock_api.get(f"{V2_BASE}/pomodoros/timeline").mock(
            return_value=httpx.Response(
                200, json={"sessions": [{"id": "p1", "start": "2026-02-22"}]}
            )
        )
        result = await client.v2_get("/pomodoros/timeline")
        assert "sessions" in result


class TestFocusSave:
    @pytest.mark.anyio
    async def test_save_basic(self, client: TickTickClient, mock_api: respx.MockRouter):
        route = mock_api.post(f"{V2_BASE}/batch/pomodoro").mock(
            return_value=httpx.Response(200, json={"id2etag": {}})
        )
        result = await client.v2_post(
            "/batch/pomodoro",
            {
                "add": [
                    {
                        "id": "test123",
                        "startTime": "2026-02-22T14:00:00.000+0000",
                        "endTime": "2026-02-22T14:25:00.000+0000",
                        "status": 1,
                        "pauseDuration": 0,
                        "tasks": [
                            {
                                "startTime": "2026-02-22T14:00:00.000+0000",
                                "endTime": "2026-02-22T14:25:00.000+0000",
                                "title": "",
                            }
                        ],
                        "note": "",
                    }
                ],
                "update": [],
                "delete": [],
            },
        )
        assert route.called
        request = route.calls[0].request
        body = httpx.Request("POST", request.url, content=request.content).content
        import json

        parsed = json.loads(body)
        record = parsed["add"][0]
        assert record["status"] == 1
        assert record["pauseDuration"] == 0
        assert len(record["tasks"]) == 1
        assert result == {"id2etag": {}}

    @pytest.mark.anyio
    async def test_save_with_task(self, client: TickTickClient, mock_api: respx.MockRouter):
        route = mock_api.post(f"{V2_BASE}/batch/pomodoro").mock(
            return_value=httpx.Response(200, json={"id2etag": {}})
        )
        await client.v2_post(
            "/batch/pomodoro",
            {
                "add": [
                    {
                        "id": "test456",
                        "startTime": "2026-02-22T14:00:00.000+0000",
                        "endTime": "2026-02-22T14:25:00.000+0000",
                        "status": 1,
                        "pauseDuration": 0,
                        "tasks": [
                            {
                                "startTime": "2026-02-22T14:00:00.000+0000",
                                "endTime": "2026-02-22T14:25:00.000+0000",
                                "title": "",
                                "taskId": "task1",
                                "projectId": "proj1",
                            }
                        ],
                        "note": "Deep work session",
                    }
                ],
                "update": [],
                "delete": [],
            },
        )
        import json

        parsed = json.loads(route.calls[0].request.content)
        task = parsed["add"][0]["tasks"][0]
        assert task["taskId"] == "task1"
        assert task["projectId"] == "proj1"
        assert parsed["add"][0]["note"] == "Deep work session"
