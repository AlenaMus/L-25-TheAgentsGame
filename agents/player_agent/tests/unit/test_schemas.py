"""
Unit tests for Pydantic schemas.

Tests validation rules for:
- JSONRPCRequest
- JSONRPCResponse
- JSONRPCError
- MessageEnvelope
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from player_agent.mcp.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MessageEnvelope
)


class TestJSONRPCRequest:
    """Test JSONRPCRequest schema validation."""

    def test_valid_request_with_all_fields(self):
        """Test valid request with all fields."""
        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="test_method",
            params={"key": "value"},
            id=1
        )

        assert req.jsonrpc == "2.0"
        assert req.method == "test_method"
        assert req.params == {"key": "value"}
        assert req.id == 1

    def test_valid_request_without_params(self):
        """Test valid request without params (notification)."""
        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="test_method",
            id=1
        )

        assert req.params == {}

    def test_valid_request_without_id(self):
        """Test valid request without id."""
        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="test_method"
        )

        assert req.id is None

    def test_invalid_jsonrpc_version(self):
        """Test that invalid JSON-RPC version fails validation."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(
                jsonrpc="1.0",  # Invalid version
                method="test_method"
            )

    def test_empty_method_name_fails(self):
        """Test that empty method name fails validation."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(
                jsonrpc="2.0",
                method=""  # Empty method
            )

    def test_missing_method_fails(self):
        """Test that missing method fails validation."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(jsonrpc="2.0")


class TestJSONRPCError:
    """Test JSONRPCError schema validation."""

    def test_valid_error_with_code_and_message(self):
        """Test valid error with required fields."""
        error = JSONRPCError(
            code=-32600,
            message="Invalid Request"
        )

        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data is None

    def test_valid_error_with_data(self):
        """Test error with additional data."""
        error = JSONRPCError(
            code=-32602,
            message="Invalid params",
            data="Missing required field: match_id"
        )

        assert error.data == "Missing required field: match_id"

    def test_standard_error_codes(self):
        """Test all standard JSON-RPC error codes."""
        codes = {
            -32700: "Parse error",
            -32600: "Invalid Request",
            -32601: "Method not found",
            -32602: "Invalid params",
            -32603: "Internal error"
        }

        for code, message in codes.items():
            error = JSONRPCError(code=code, message=message)
            assert error.code == code


class TestJSONRPCResponse:
    """Test JSONRPCResponse schema validation."""

    def test_valid_success_response(self):
        """Test valid success response."""
        resp = JSONRPCResponse(
            jsonrpc="2.0",
            result={"status": "ok"},
            id=1
        )

        assert resp.result == {"status": "ok"}
        assert resp.error is None
        assert resp.id == 1

    def test_valid_error_response(self):
        """Test valid error response."""
        error = JSONRPCError(code=-32601, message="Method not found")
        resp = JSONRPCResponse(
            jsonrpc="2.0",
            error=error,
            id=1
        )

        assert resp.result is None
        assert resp.error.code == -32601
        assert resp.id == 1

    def test_response_without_id(self):
        """Test response can have null id."""
        resp = JSONRPCResponse(
            jsonrpc="2.0",
            result={"data": "test"},
            id=None
        )

        assert resp.id is None


class TestMessageEnvelope:
    """Test MessageEnvelope schema validation."""

    def test_valid_envelope_all_fields(self):
        """Test valid envelope with all fields."""
        envelope = MessageEnvelope(
            protocol="league.v2",
            message_type="GAME_INVITATION",
            sender="referee:REF01",
            timestamp="20250121T100000Z",
            conversation_id="convr1m1001",
            auth_token="tok_abc123"
        )

        assert envelope.protocol == "league.v2"
        assert envelope.message_type == "GAME_INVITATION"
        assert envelope.sender == "referee:REF01"

    def test_valid_protocol_versions(self):
        """Test various valid protocol versions."""
        for version in ["league.v1", "league.v2", "league.v10"]:
            envelope = MessageEnvelope(
                protocol=version,
                message_type="TEST",
                sender="player:P01",
                timestamp="20250121T100000Z",
                conversation_id="test"
            )
            assert envelope.protocol == version

    def test_invalid_protocol_format_fails(self):
        """Test that invalid protocol format fails."""
        with pytest.raises(ValidationError):
            MessageEnvelope(
                protocol="invalid_protocol",
                message_type="TEST",
                sender="player:P01",
                timestamp="20250121T100000Z",
                conversation_id="test"
            )

    def test_valid_message_types(self):
        """Test various valid message types."""
        types = [
            "GAME_INVITATION",
            "GAME_JOIN_ACK",
            "CHOOSE_PARITY_CALL",
            "CHOOSE_PARITY_RESPONSE",
            "GAME_OVER"
        ]

        for msg_type in types:
            envelope = MessageEnvelope(
                protocol="league.v2",
                message_type=msg_type,
                sender="player:P01",
                timestamp="20250121T100000Z",
                conversation_id="test"
            )
            assert envelope.message_type == msg_type

    def test_invalid_message_type_fails(self):
        """Test lowercase message type fails."""
        with pytest.raises(ValidationError):
            MessageEnvelope(
                protocol="league.v2",
                message_type="game_invitation",  # lowercase
                sender="player:P01",
                timestamp="20250121T100000Z",
                conversation_id="test"
            )

    def test_valid_sender_formats(self):
        """Test all valid sender formats."""
        senders = [
            "league_manager",
            "referee:REF01",
            "player:P01"
        ]

        for sender in senders:
            envelope = MessageEnvelope(
                protocol="league.v2",
                message_type="TEST",
                sender=sender,
                timestamp="20250121T100000Z",
                conversation_id="test"
            )
            assert envelope.sender == sender

    def test_invalid_sender_format_fails(self):
        """Test that invalid sender format fails."""
        with pytest.raises(ValidationError):
            MessageEnvelope(
                protocol="league.v2",
                message_type="TEST",
                sender="invalid_sender",
                timestamp="20250121T100000Z",
                conversation_id="test"
            )

    def test_utc_timestamp_validation(self):
        """Test UTC timestamp validation."""
        envelope = MessageEnvelope(
            protocol="league.v2",
            message_type="TEST",
            sender="player:P01",
            timestamp="20250121T100000Z",
            conversation_id="test"
        )

        assert envelope.timestamp == "20250121T100000Z"

    def test_conversation_id_length_validation(self):
        """Test conversation_id length constraints."""
        # Valid length
        envelope = MessageEnvelope(
            protocol="league.v2",
            message_type="TEST",
            sender="player:P01",
            timestamp="20250121T100000Z",
            conversation_id="a" * 100  # Max 100 chars
        )
        assert len(envelope.conversation_id) == 100

        # Too long
        with pytest.raises(ValidationError):
            MessageEnvelope(
                protocol="league.v2",
                message_type="TEST",
                sender="player:P01",
                timestamp="20250121T100000Z",
                conversation_id="a" * 101  # > 100 chars
            )
