"""Tests for the opencode2claude Python proxy (Claude /v1/messages format)."""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

# Patch settings before importing the app
import os
os.environ["API_KEY"] = "test-key"
os.environ["OPENCODE_PROXY_MANAGE_BACKEND"] = "false"
os.environ["OPENCODE_INTERNAL_ALLOWED_TOOLS"] = "web_fetch,filesystem"
os.environ["OPENCODE_TOOL_DISCOVERY_FIXTURE"] = "web_fetch,filesystem,bash"
os.environ["OPENCODE_HEALTH_DETAILS_ENABLED"] = "true"
os.environ["OPENCODE_HEALTH_DETAILS_REQUIRE_AUTH"] = "true"
os.environ["OPENCODE_METRICS_ENABLED"] = "true"
os.environ["OPENCODE_METRICS_REQUIRE_AUTH"] = "true"

from python_src.main import app, _internal_tool_metrics


AUTH_HEADER = {"Authorization": "Bearer test-key"}


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset internal tool metrics before each test."""
    for key in _internal_tool_metrics:
        _internal_tool_metrics[key] = 0
    yield


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# --- Health ---

@pytest.mark.asyncio
async def test_health(client):
    with patch("python_src.main.process_manager.check_health", new_callable=AsyncMock, return_value=True):
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


# --- Health Details ---

@pytest.mark.asyncio
async def test_health_details_returns_diagnostics_when_authorized(client):
    resp = await client.get("/health/details", headers=AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["proxy"] is True
    assert "internal_tools" in body
    assert body["internal_tools"]["config"]["metrics_enabled"] is True


@pytest.mark.asyncio
async def test_health_details_returns_401_without_auth(client):
    resp = await client.get("/health/details")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_details_returns_404_when_disabled(client):
    from python_src.config import settings
    original = settings.HEALTH_DETAILS_ENABLED
    settings.HEALTH_DETAILS_ENABLED = False
    try:
        resp = await client.get("/health/details", headers=AUTH_HEADER)
        assert resp.status_code == 404
    finally:
        settings.HEALTH_DETAILS_ENABLED = original


# --- Metrics ---

@pytest.mark.asyncio
async def test_metrics_returns_prometheus_when_authorized(client):
    resp = await client.get("/metrics", headers=AUTH_HEADER)
    assert resp.status_code == 200
    text = resp.text
    assert "opencode_internal_tool_mode_requests_total" in text


@pytest.mark.asyncio
async def test_metrics_returns_401_without_auth(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_metrics_returns_404_when_disabled(client):
    from python_src.config import settings
    original = settings.METRICS_ENABLED
    settings.METRICS_ENABLED = False
    try:
        resp = await client.get("/metrics", headers=AUTH_HEADER)
        assert resp.status_code == 404
    finally:
        settings.METRICS_ENABLED = original


# --- Models ---

@pytest.mark.asyncio
async def test_models_returns_list(client):
    mock_providers = {
        "providers": [{
            "id": "opencode",
            "models": {
                "test-model": {"name": "Test Model"}
            }
        }]
    }
    with patch("python_src.main.opencode_client.get_providers", new_callable=AsyncMock, return_value=mock_providers):
        resp = await client.get("/v1/models", headers=AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "list"
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == "opencode/test-model"


# --- Messages (non-streaming) ---

def _make_mock_events(session_id, text="Hello"):
    """Generate a sequence of SSE events that simulate a complete response."""
    events = [
        {"type": "message.part.updated", "properties": {"part": {"sessionID": session_id, "id": "part1", "type": "text"}}},
    ]
    for ch in text:
        events.append({"type": "message.part.delta", "properties": {"sessionID": session_id, "partID": "part1", "delta": ch}})
    events.append({"type": "message.updated", "properties": {"info": {"sessionID": session_id, "finish": "stop"}}})
    return events


async def _mock_subscribe_events(events):
    for e in events:
        yield e


@pytest.mark.asyncio
async def test_messages_non_streaming(client):
    session_id = "ses_test123"
    mock_events = _make_mock_events(session_id, "Hi!")

    with patch("python_src.main.opencode_client.create_session", new_callable=AsyncMock, return_value={"id": session_id}), \
         patch("python_src.main.opencode_client.prompt", new_callable=AsyncMock), \
         patch("python_src.main.opencode_client.delete_session", new_callable=AsyncMock), \
         patch("python_src.main.opencode_client.subscribe_events", return_value=_mock_subscribe_events(mock_events)):
        resp = await client.post("/v1/messages", headers=AUTH_HEADER, json={
            "model": "opencode/test-model",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False
        })
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "assistant"
    assert body["type"] == "message"
    assert any(c["type"] == "text" and "Hi!" in c["text"] for c in body["content"])


@pytest.mark.asyncio
async def test_messages_streaming(client):
    session_id = "ses_test456"
    mock_events = _make_mock_events(session_id, "OK")

    with patch("python_src.main.opencode_client.create_session", new_callable=AsyncMock, return_value={"id": session_id}), \
         patch("python_src.main.opencode_client.prompt", new_callable=AsyncMock), \
         patch("python_src.main.opencode_client.delete_session", new_callable=AsyncMock), \
         patch("python_src.main.opencode_client.subscribe_events", return_value=_mock_subscribe_events(mock_events)):
        resp = await client.post("/v1/messages", headers=AUTH_HEADER, json={
            "model": "opencode/test-model",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True
        })
    assert resp.status_code == 200
    text = resp.text
    assert "message_start" in text
    assert "content_block_delta" in text
    assert "message_stop" in text


# --- Metrics tracking ---

@pytest.mark.asyncio
async def test_messages_increments_disabled_metrics(client):
    """When no external tools and no internal allowlist, mode is 'disabled'."""
    from python_src.config import settings
    original = settings.INTERNAL_ALLOWED_TOOLS
    settings.INTERNAL_ALLOWED_TOOLS = []
    try:
        session_id = "ses_metrics1"
        mock_events = _make_mock_events(session_id, "X")
        with patch("python_src.main.opencode_client.create_session", new_callable=AsyncMock, return_value={"id": session_id}), \
             patch("python_src.main.opencode_client.prompt", new_callable=AsyncMock), \
             patch("python_src.main.opencode_client.delete_session", new_callable=AsyncMock), \
             patch("python_src.main.opencode_client.subscribe_events", return_value=_mock_subscribe_events(mock_events)):
            await client.post("/v1/messages", headers=AUTH_HEADER, json={
                "model": "opencode/test-model",
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": False
            })
        assert _internal_tool_metrics["disabledRequests"] >= 1
    finally:
        settings.INTERNAL_ALLOWED_TOOLS = original


@pytest.mark.asyncio
async def test_messages_increments_allowlist_metrics(client):
    """When internal allowed tools are set and no external tools, mode is 'internal_allowlist'."""
    session_id = "ses_metrics2"
    mock_events = _make_mock_events(session_id, "X")
    with patch("python_src.main.opencode_client.create_session", new_callable=AsyncMock, return_value={"id": session_id}), \
         patch("python_src.main.opencode_client.prompt", new_callable=AsyncMock), \
         patch("python_src.main.opencode_client.delete_session", new_callable=AsyncMock), \
         patch("python_src.main.opencode_client.subscribe_events", return_value=_mock_subscribe_events(mock_events)):
        await client.post("/v1/messages", headers=AUTH_HEADER, json={
            "model": "opencode/test-model",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False
        })
    assert _internal_tool_metrics["internalAllowlistRequests"] >= 1
