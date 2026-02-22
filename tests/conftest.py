from __future__ import annotations

import os
from unittest.mock import patch

import pytest
import respx

from ticktick_mcp.client import TickTickClient


@pytest.fixture
def mock_api():
    """respx mock router for all TickTick API bases."""
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
async def client(mock_api: respx.MockRouter) -> TickTickClient:
    """TickTickClient with fake credentials, ready for testing."""
    c = TickTickClient(
        access_token="test-access-token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        session_token="test-session-token",
        refresh_token="test-refresh-token",
    )
    async with c:
        yield c


@pytest.fixture
def env_vars():
    """Set required environment variables for server tests."""
    env = {
        "TICKTICK_ACCESS_TOKEN": "test-access-token",
        "TICKTICK_CLIENT_ID": "test-client-id",
        "TICKTICK_CLIENT_SECRET": "test-client-secret",
        "TICKTICK_V2_SESSION_TOKEN": "test-session-token",
    }
    with patch.dict(os.environ, env):
        yield env
