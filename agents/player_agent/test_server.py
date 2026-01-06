"""
Quick test script for MCP server endpoints.
"""

import requests
import json
from datetime import datetime, timezone


def test_health_check():
    """Test health check endpoint."""
    print("\n1. Testing /health endpoint...")
    response = requests.get("http://localhost:8101/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health check passed")


def test_initialize():
    """Test MCP initialization."""
    print("\n2. Testing /initialize endpoint...")
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {},
        "id": 1
    }
    response = requests.post(
        "http://localhost:8101/initialize",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert "serverInfo" in result
    print("✓ Initialize passed")


def test_handle_game_invitation():
    """Test handle_game_invitation tool."""
    print("\n3. Testing handle_game_invitation tool...")
    payload = {
        "jsonrpc": "2.0",
        "method": "handle_game_invitation",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "conversation_id": "test_conv_001",
            "auth_token": "test_token",
            "league_id": "league_2025_test",
            "round_id": 1,
            "match_id": "TEST_M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
            "player_id": "P01"
        },
        "id": 100
    }
    response = requests.post(
        "http://localhost:8101/mcp",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["message_type"] == "GAME_JOIN_ACK"
    assert result["accept"] == True
    print("✓ handle_game_invitation passed")


def test_choose_parity():
    """Test choose_parity tool."""
    print("\n4. Testing choose_parity tool...")
    payload = {
        "jsonrpc": "2.0",
        "method": "choose_parity",
        "params": {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": "referee:REF01",
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "conversation_id": "test_conv_001",
            "auth_token": "test_token",
            "match_id": "TEST_M1",
            "player_id": "P01",
            "game_type": "even_odd",
            "context": {
                "opponent_id": "P02",
                "round_id": 1,
                "your_standings": {
                    "wins": 0,
                    "losses": 0,
                    "draws": 0
                }
            },
            "deadline": "20250121T10:30:00Z"
        },
        "id": 101
    }
    response = requests.post(
        "http://localhost:8101/mcp",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["message_type"] == "CHOOSE_PARITY_RESPONSE"
    assert result["parity_choice"] in ["even", "odd"]
    print(f"✓ choose_parity passed (choice: {result['parity_choice']})")


def test_notify_match_result():
    """Test notify_match_result tool."""
    print("\n5. Testing notify_match_result tool...")
    payload = {
        "jsonrpc": "2.0",
        "method": "notify_match_result",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": "referee:REF01",
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "conversation_id": "test_conv_001",
            "auth_token": "test_token",
            "match_id": "TEST_M1",
            "game_type": "even_odd",
            "player_id": "P01",
            "game_result": {
                "status": "WIN",
                "winner_player_id": "P01",
                "drawn_number": 8,
                "number_parity": "even",
                "choices": {
                    "P01": "even",
                    "P02": "odd"
                },
                "reason": "P01 chose even, number was 8 (even)"
            }
        },
        "id": 102
    }
    response = requests.post(
        "http://localhost:8101/mcp",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["acknowledged"] == True
    print("✓ notify_match_result passed")


def test_invalid_method():
    """Test invalid method error."""
    print("\n6. Testing invalid method (error handling)...")
    payload = {
        "jsonrpc": "2.0",
        "method": "nonexistent_method",
        "params": {},
        "id": 103
    }
    response = requests.post(
        "http://localhost:8101/mcp",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "error" in response.json()
    assert response.json()["error"]["code"] == -32601
    print("✓ Error handling passed")


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)

    try:
        test_health_check()
        test_initialize()
        test_handle_game_invitation()
        test_choose_parity()
        test_notify_match_result()
        test_invalid_method()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Is it running on port 8101?")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
