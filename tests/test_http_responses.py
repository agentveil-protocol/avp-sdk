"""Tests for HTTP response handling in AVPAgent._handle_response."""

import pytest
from unittest.mock import MagicMock

from agentveil.agent import AVPAgent
from agentveil.exceptions import (
    AVPAuthError,
    AVPNotFoundError,
    AVPRateLimitError,
    AVPValidationError,
    AVPServerError,
    AVPError,
)


def _make_response(status_code: int, json_data=None, text="", headers=None):
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


class TestHandleResponse:
    """Response parsing and exception mapping."""

    def setup_method(self):
        self.agent = AVPAgent.create("https://example.com", name="test", save=False)

    def test_200_returns_json(self):
        resp = _make_response(200, {"status": "ok"})
        result = self.agent._handle_response(resp)
        assert result == {"status": "ok"}

    def test_201_returns_json(self):
        resp = _make_response(201, {"id": "case-1", "status": "OPEN"})
        result = self.agent._handle_response(resp)
        assert result == {"id": "case-1", "status": "OPEN"}

    def test_raw_json_response_preserves_exact_text(self):
        raw = '{"proof":{"type":"DataIntegrityProof"},"receipt_id":"urn:uuid:abc"}'
        resp = _make_response(200, {"receipt_id": "urn:uuid:abc"}, text=raw)
        result = self.agent._handle_raw_json_response(resp)
        assert result == raw

    def test_raw_json_response_preserves_spacing_and_trailing_whitespace(self):
        raw = '{  "receipt_id" : "urn:uuid:abc", "status" : "SUCCESS"  }\n  '
        resp = _make_response(200, {"receipt_id": "urn:uuid:abc"}, text=raw)
        result = self.agent._handle_raw_json_response(resp)
        assert result == raw

    def test_raw_json_response_accepts_201(self):
        raw = '{"id":"urn:uuid:case","status":"OPEN"}'
        resp = _make_response(201, {"id": "urn:uuid:case", "status": "OPEN"}, text=raw)
        result = self.agent._handle_raw_json_response(resp)
        assert result == raw

    def test_raw_json_response_rejects_non_json_success(self):
        resp = _make_response(200, json_data=None, text="not json")
        with pytest.raises(AVPServerError) as exc_info:
            self.agent._handle_raw_json_response(resp)
        assert exc_info.value.status_code == 200

    def test_401_raises_auth_error(self):
        resp = _make_response(401, {"detail": "bad signature"})
        with pytest.raises(AVPAuthError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 401

    def test_403_raises_auth_error(self):
        resp = _make_response(403, {"detail": "forbidden"})
        with pytest.raises(AVPAuthError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 403

    def test_404_raises_not_found(self):
        resp = _make_response(404, {"detail": "agent not found"})
        with pytest.raises(AVPNotFoundError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 404

    def test_409_raises_validation_error(self):
        resp = _make_response(409, {"detail": "already registered"})
        with pytest.raises(AVPValidationError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 409

    def test_429_raises_rate_limit(self):
        resp = _make_response(
            429,
            {"detail": "too many requests"},
            headers={"Retry-After": "17"},
        )
        with pytest.raises(AVPRateLimitError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.retry_after == 17

    def test_400_raises_validation_error(self):
        resp = _make_response(400, {"detail": "invalid input"})
        with pytest.raises(AVPValidationError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 400

    def test_500_raises_server_error(self):
        resp = _make_response(500, {"detail": "internal error"})
        with pytest.raises(AVPServerError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 500

    def test_502_raises_server_error(self):
        resp = _make_response(502, {"detail": "bad gateway"})
        with pytest.raises(AVPServerError):
            self.agent._handle_response(resp)

    def test_unexpected_status_raises_avp_error(self):
        resp = _make_response(418, {"detail": "teapot"})
        with pytest.raises(AVPError) as exc_info:
            self.agent._handle_response(resp)
        assert exc_info.value.status_code == 418

    def test_non_json_error_response(self):
        resp = _make_response(500, json_data=None, text="nginx error")
        with pytest.raises(AVPServerError):
            self.agent._handle_response(resp)
