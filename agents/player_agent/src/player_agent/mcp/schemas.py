"""
Pydantic schemas for JSON-RPC 2.0 and MCP protocol messages.

Defines request/response structures and validation rules.
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Optional, Dict
from datetime import datetime


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 request schema.

    Attributes:
        jsonrpc: Protocol version (always "2.0")
        method: Method name to invoke
        params: Method parameters (optional)
        id: Request identifier (optional for notifications)

    Example:
        >>> req = JSONRPCRequest(
        ...     jsonrpc="2.0",
        ...     method="choose_parity",
        ...     params={"match_id": "R1M1"},
        ...     id=1
        ... )
    """

    jsonrpc: str = Field(..., pattern=r"^2\.0$")
    method: str = Field(..., min_length=1)
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    id: Optional[int] = None


class JSONRPCError(BaseModel):
    """
    JSON-RPC 2.0 error object.

    Attributes:
        code: Error code
        message: Error message
        data: Additional error data (optional)

    Standard error codes:
        -32700: Parse error
        -32600: Invalid Request
        -32601: Method not found
        -32602: Invalid params
        -32603: Internal error
    """

    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """
    JSON-RPC 2.0 response schema.

    Attributes:
        jsonrpc: Protocol version (always "2.0")
        result: Result data (if successful)
        error: Error object (if failed)
        id: Request identifier

    Example:
        >>> resp = JSONRPCResponse(
        ...     jsonrpc="2.0",
        ...     result={"choice": "even"},
        ...     id=1
        ... )
    """

    jsonrpc: str = Field(default="2.0", pattern=r"^2\.0$")
    result: Optional[Dict[str, Any]] = None
    error: Optional[JSONRPCError] = None
    id: Optional[int] = None

    @validator('result', 'error')
    def check_result_or_error(cls, v, values):
        """Ensure exactly one of result or error is set."""
        if 'result' in values and values['result'] is not None and v is not None:
            raise ValueError('Cannot have both result and error')
        return v


class MessageEnvelope(BaseModel):
    """
    Base message envelope for league protocol.

    All protocol messages include these fields.

    Attributes:
        protocol: Protocol version
        message_type: Type of message
        sender: Message originator
        timestamp: UTC timestamp
        conversation_id: Conversation tracking ID
        auth_token: Authentication token (optional)

    Example:
        >>> envelope = MessageEnvelope(
        ...     protocol="league.v2",
        ...     message_type="GAME_INVITATION",
        ...     sender="referee:REF01",
        ...     timestamp="20250121T10:00:00Z",
        ...     conversation_id="convr1m1001"
        ... )
    """

    protocol: str = Field(..., pattern=r"^league\.v\d+$")
    message_type: str = Field(..., pattern=r"^[A-Z_]+$")
    sender: str = Field(
        ...,
        pattern=r"^(league_manager|referee:\w+|player:\w+)$"
    )
    timestamp: str
    conversation_id: str = Field(..., min_length=1, max_length=100)
    auth_token: Optional[str] = None

    @validator('timestamp')
    def validate_utc_timestamp(cls, v):
        """
        Ensure timestamp is in UTC timezone.

        Args:
            v: Timestamp string

        Returns:
            str: Validated timestamp

        Raises:
            ValueError: If timestamp is not UTC
        """
        try:
            # Parse timestamp (support both formats)
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))

            # Check UTC (offset must be 0)
            if dt.utcoffset().total_seconds() != 0:
                raise ValueError("Timestamp must be in UTC timezone")

            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid timestamp format: {str(e)}")
