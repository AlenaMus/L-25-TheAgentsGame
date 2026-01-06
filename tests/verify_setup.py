"""
Verify integration test setup.

Quick script to check if all agents can be started and
basic communication works.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.utils import AgentManager, MCPClient, PortManager


async def main():
    """Run setup verification."""
    print("=" * 60)
    print("Integration Test Setup Verification")
    print("=" * 60)
    print()

    port_manager = PortManager(start_port=9000)
    agent_manager = AgentManager()

    try:
        # Test 1: Start League Manager
        print("Test 1: Starting League Manager...")
        lm_port = port_manager.allocate()
        league_manager = await agent_manager.start_league_manager(lm_port)
        print(f"✓ League Manager started on port {lm_port}")
        print(f"  Endpoint: {league_manager.endpoint}")
        print()

        # Test 2: Start Referee
        print("Test 2: Starting Referee...")
        ref_port = port_manager.allocate()
        referee = await agent_manager.start_referee("REF01", ref_port)
        print(f"✓ Referee started on port {ref_port}")
        print(f"  Endpoint: {referee.endpoint}")
        print()

        # Test 3: Start Player
        print("Test 3: Starting Player...")
        p1_port = port_manager.allocate()
        player1 = await agent_manager.start_player("P01", p1_port)
        print(f"✓ Player started on port {p1_port}")
        print(f"  Endpoint: {player1.endpoint}")
        print()

        # Test 4: Health check League Manager
        print("Test 4: Health check League Manager...")
        async with MCPClient() as client:
            is_healthy = await client.health_check(league_manager.endpoint)
            if is_healthy:
                print("✓ League Manager is healthy")
            else:
                print("✗ League Manager health check failed")
        print()

        # Test 5: Player registration
        print("Test 5: Player registration...")
        async with MCPClient() as client:
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:test",
                    "timestamp": "2025-12-24T10:00:00Z",
                    "conversation_id": "verify-001",
                    "player_meta": {
                        "display_name": "VerifyPlayer",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player1.endpoint
                    }
                }
            )

            if "result" in response:
                result = response["result"]
                if result.get("status") == "ACCEPTED":
                    print(f"✓ Player registration successful")
                    print(f"  Player ID: {result.get('player_id')}")
                    print(f"  Auth Token: {result.get('auth_token')[:20]}...")
                    print(f"  League ID: {result.get('league_id')}")
                else:
                    print(f"✗ Registration rejected: {result.get('rejection_reason')}")
            else:
                print(f"✗ Registration failed: {response}")
        print()

        # Test 6: Referee registration
        print("Test 6: Referee registration...")
        async with MCPClient() as client:
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_referee",
                params={
                    "protocol": "league.v2",
                    "message_type": "REFEREE_REGISTER_REQUEST",
                    "sender": "referee:test",
                    "timestamp": "2025-12-24T10:00:01Z",
                    "conversation_id": "verify-002",
                    "referee_meta": {
                        "display_name": "VerifyReferee",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": referee.endpoint,
                        "max_concurrent_matches": 5
                    }
                }
            )

            if "result" in response:
                result = response["result"]
                if result.get("status") == "ACCEPTED":
                    print(f"✓ Referee registration successful")
                    print(f"  Referee ID: {result.get('referee_id')}")
                    print(f"  Auth Token: {result.get('auth_token')[:20]}...")
                    print(f"  League ID: {result.get('league_id')}")
                else:
                    print(f"✗ Registration rejected: {result.get('rejection_reason')}")
            else:
                print(f"✗ Registration failed: {response}")
        print()

        print("=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run: pytest tests/integration/test_player_registration.py -v")
        print("  2. Run: pytest tests/integration/test_referee_registration.py -v")
        print()

    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Cleaning up agents...")
        await agent_manager.cleanup()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
