"""Tests for AVPAgent.integration_preflight."""

from unittest.mock import MagicMock, patch

import httpx
from nacl.signing import SigningKey

from agentveil import AVPAgent, IntegrationPreflightReport


def _make_agent() -> AVPAgent:
    sk = SigningKey.generate()
    return AVPAgent("http://localhost:8000", bytes(sk), name="preflight-test", timeout=1.0)


def _response(status_code: int, payload: dict | None = None, headers: dict | None = None):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = "" if payload is None else str(payload)
    resp.json.return_value = payload or {}
    return resp


def test_integration_preflight_ready_uses_safe_signed_read_without_query_params():
    agent = _make_agent()
    calls = []

    def mock_get(url, **kwargs):
        calls.append({"url": url, **kwargs})
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": True, "status": "active"})
        if url == "/v1/remediation/cases":
            return _response(200, {"items": [], "count": 0, "has_more": False})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert isinstance(report, IntegrationPreflightReport)
    assert report.ready is True
    assert report.status == "ready"
    assert report.registered is True
    assert report.verified is True
    assert report.signed_request_ok is True

    signed_call = calls[2]
    assert signed_call["url"] == "/v1/remediation/cases"
    assert "Authorization" in signed_call["headers"]
    assert 'v="2"' not in signed_call["headers"]["Authorization"]
    assert "params" not in signed_call


def test_integration_preflight_maps_unknown_did_401_as_unregistered():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(404, {"detail": "Agent not found"})
        if url == "/v1/remediation/cases":
            return _response(401, {"detail": "Missing or invalid Authorization header"})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "unregistered"
    assert report.registered is False
    assert report.verified is False
    assert report.status_code == 401
    assert "Register and verify" in report.next_action


def test_integration_preflight_unverified_agent_is_not_ready_even_if_signed_read_succeeds():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": False, "status": "active"})
        if url == "/v1/remediation/cases":
            return _response(200, {"items": [], "count": 0, "has_more": False})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "unverified_or_forbidden"
    assert report.registered is True
    assert report.verified is False
    assert report.signed_request_ok is True


def test_integration_preflight_registered_agent_401_is_signature_invalid():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": True, "status": "active"})
        if url == "/v1/remediation/cases":
            return _response(401, {"detail": "Invalid signature"})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "signature_invalid"
    assert report.registered is True
    assert report.verified is True
    assert report.status_code == 401
    assert "local key matches" in report.next_action


def test_integration_preflight_suspended_agent_gets_specific_status():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": True, "status": "SUSPENDED"})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "agent_suspended"
    assert report.registered is True
    assert report.verified is True
    assert report.agent_status == "SUSPENDED"
    assert "suspended or revoked" in report.next_action


def test_integration_preflight_maps_403_as_unverified_or_forbidden():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": False, "status": "active"})
        if url == "/v1/remediation/cases":
            return _response(403, {"detail": "Agent not verified"})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "unverified_or_forbidden"
    assert report.registered is True
    assert report.verified is False
    assert report.status_code == 403
    assert "Verify the agent DID" in report.next_action


def test_integration_preflight_malformed_agent_lookup_json_does_not_raise():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            resp = _response(200)
            resp.text = "not json"
            resp.json.side_effect = ValueError("malformed")
            return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "unexpected_response"
    assert report.status_code == 200
    assert report.detail == "not json"
    assert "malformed JSON" in report.next_action


def test_integration_preflight_maps_429_with_retry_guidance():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": True, "status": "active"})
        if url == "/v1/remediation/cases":
            return _response(429, {"detail": "Rate limit exceeded"}, headers={"Retry-After": "17"})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "rate_limited"
    assert report.retry_after == 17
    assert "Wait 17 seconds" in report.next_action


def test_integration_preflight_maps_503_as_backend_or_config_unavailable():
    agent = _make_agent()

    def mock_get(url, **kwargs):
        if url == "/v1/health":
            return _response(200, {"status": "ok", "database": "ok"})
        if url == f"/v1/agents/{agent.did}":
            return _response(200, {"did": agent.did, "is_verified": True, "status": "active"})
        if url == "/v1/remediation/cases":
            return _response(503, {"detail": "Execution unavailable"})
        raise AssertionError(f"unexpected URL: {url}")

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "backend_or_config_unavailable"
    assert report.status_code == 503
    assert "do not retry aggressively" in report.next_action


def test_integration_preflight_maps_network_failure_as_api_unreachable():
    agent = _make_agent()

    with patch.object(httpx.Client, "get", side_effect=httpx.ConnectError("offline")):
        report = agent.integration_preflight()

    assert report.ready is False
    assert report.status == "api_unreachable"
    assert report.api_reachable is False
    assert "base_url" in report.next_action
