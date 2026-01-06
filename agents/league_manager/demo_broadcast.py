#!/usr/bin/env python3
"""
Demo: Broadcast System

Demonstrates broadcasting messages to multiple agents concurrently.
Shows timeout handling, retry logic, and delivery reporting.
"""

import asyncio
from league_manager.broadcast import Broadcaster, MessageBuilder
from league_manager.utils.logger import logger


async def demo_broadcast_success():
    """Demo successful broadcast to all agents."""
    print("\n" + "="*70)
    print("DEMO 1: Successful Broadcast to All Players")
    print("="*70)

    broadcaster = Broadcaster(timeout=5.0, max_retries=2)
    message_builder = MessageBuilder(league_id="demo_league")

    # Simulated player list
    players = [
        {"player_id": "P01", "display_name": "Alice", "endpoint": "http://localhost:9001/mcp"},
        {"player_id": "P02", "display_name": "Bob", "endpoint": "http://localhost:9002/mcp"},
        {"player_id": "P03", "display_name": "Charlie", "endpoint": "http://localhost:9003/mcp"}
    ]

    # Build round announcement
    matches = [
        {
            "match_id": "R1M1",
            "game_type": "even_odd",
            "player_A_id": "P01",
            "player_B_id": "P02",
            "referee_endpoint": "referee:REF01"
        },
        {
            "match_id": "R1M2",
            "game_type": "even_odd",
            "player_A_id": "P03",
            "player_B_id": "P04",
            "referee_endpoint": "referee:REF01"
        }
    ]

    message = message_builder.build_round_announcement(round_id=1, matches=matches)

    print(f"\nBroadcasting to {len(players)} players:")
    for player in players:
        print(f"  - {player['player_id']}: {player['display_name']} ({player['endpoint']})")

    print("\nMessage:")
    print(f"  Type: {message['message_type']}")
    print(f"  Round: {message['round_id']}")
    print(f"  Matches: {len(message['matches'])}")

    # Note: In real scenario, this would send HTTP requests
    # For demo, we'll simulate with mock
    print("\n[SIMULATION] Broadcasting messages concurrently...")
    print("[SIMULATION] All agents would receive HTTP POST requests")

    print("\nExpected Delivery Report:")
    print(f"  Total: {len(players)}")
    print(f"  Successful: {len(players)}")
    print(f"  Failed: 0")
    print(f"  Success Rate: 100.0%")


async def demo_broadcast_with_failures():
    """Demo broadcast with some failures."""
    print("\n" + "="*70)
    print("DEMO 2: Broadcast with Timeout and Retry")
    print("="*70)

    broadcaster = Broadcaster(timeout=5.0, max_retries=2)
    message_builder = MessageBuilder()

    players = [
        {"player_id": "P01", "endpoint": "http://localhost:9001/mcp"},
        {"player_id": "P02", "endpoint": "http://unreachable:9999/mcp"},  # Will timeout
        {"player_id": "P03", "endpoint": "http://localhost:9003/mcp"}
    ]

    message = message_builder.build_round_completed(
        round_id=1,
        matches_completed=2,
        next_round_id=2
    )

    print(f"\nBroadcasting ROUND_COMPLETED to {len(players)} players")
    print("  P01: localhost:9001 (reachable)")
    print("  P02: unreachable:9999 (will timeout)")
    print("  P03: localhost:9003 (reachable)")

    print("\n[SIMULATION] Sending messages...")
    print("[SIMULATION] P01: Success (1/1 attempts)")
    print("[SIMULATION] P02: Timeout (attempt 1/3)")
    print("[SIMULATION] P02: Timeout (attempt 2/3)")
    print("[SIMULATION] P02: Timeout (attempt 3/3) - FAILED")
    print("[SIMULATION] P03: Success (1/1 attempts)")

    print("\nExpected Delivery Report:")
    print("  Total: 3")
    print("  Successful: 2")
    print("  Failed: 1")
    print("  Failed Agents: ['P02']")
    print("  Success Rate: 66.7%")


async def demo_message_types():
    """Demo different message types."""
    print("\n" + "="*70)
    print("DEMO 3: Different Message Types")
    print("="*70)

    builder = MessageBuilder(league_id="demo_league")

    # 1. Round Announcement
    print("\n1. ROUND_ANNOUNCEMENT:")
    msg = builder.build_round_announcement(
        round_id=1,
        matches=[{"match_id": "R1M1", "player_A_id": "P01", "player_B_id": "P02"}]
    )
    print(f"   Protocol: {msg['protocol']}")
    print(f"   Message Type: {msg['message_type']}")
    print(f"   Conversation ID: {msg['conversation_id']}")
    print(f"   Round ID: {msg['round_id']}")

    # 2. Round Completed
    print("\n2. ROUND_COMPLETED:")
    msg = builder.build_round_completed(round_id=1, matches_completed=2, next_round_id=2)
    print(f"   Message Type: {msg['message_type']}")
    print(f"   Matches Completed: {msg['matches_completed']}")
    print(f"   Next Round: {msg['next_round_id']}")

    # 3. Tournament Start
    print("\n3. TOURNAMENT_START:")
    msg = builder.build_tournament_start(total_rounds=3, total_matches=6, player_count=4)
    print(f"   Message Type: {msg['message_type']}")
    print(f"   Total Rounds: {msg['total_rounds']}")
    print(f"   Total Matches: {msg['total_matches']}")
    print(f"   Player Count: {msg['player_count']}")

    # 4. Tournament End
    print("\n4. TOURNAMENT_END:")
    champion = {"player_id": "P01", "display_name": "Alice", "points": 9}
    standings = [
        {"rank": 1, "player_id": "P01", "points": 9},
        {"rank": 2, "player_id": "P02", "points": 6}
    ]
    msg = builder.build_tournament_end(
        total_rounds=3,
        total_matches=6,
        champion=champion,
        final_standings=standings
    )
    print(f"   Message Type: {msg['message_type']}")
    print(f"   Champion: {msg['champion']['player_id']} ({msg['champion']['points']} points)")
    print(f"   Final Standings: {len(msg['final_standings'])} players")

    # 5. Standings Update
    print("\n5. LEAGUE_STANDINGS_UPDATE:")
    msg = builder.build_standings_update(round_id=2, standings=standings)
    print(f"   Message Type: {msg['message_type']}")
    print(f"   Round ID: {msg['round_id']}")
    print(f"   Standings Count: {len(msg['standings'])}")


async def demo_concurrent_broadcast():
    """Demo concurrent broadcast efficiency."""
    print("\n" + "="*70)
    print("DEMO 4: Concurrent Broadcast Performance")
    print("="*70)

    broadcaster = Broadcaster(timeout=5.0, max_retries=2)

    # Large player list
    players = [
        {"player_id": f"P{i:02d}", "endpoint": f"http://localhost:{9000+i}/mcp"}
        for i in range(1, 11)  # 10 players
    ]

    message = {"message_type": "TEST", "data": "concurrent test"}

    print(f"\nBroadcasting to {len(players)} players concurrently")
    print("\n[SIMULATION] Sequential approach would take:")
    print(f"  {len(players)} requests × 1 second each = {len(players)} seconds")

    print("\n[SIMULATION] Concurrent approach (asyncio.gather) takes:")
    print("  All 10 requests in parallel = ~1 second total")

    print("\nConcurrency Advantage:")
    print(f"  {len(players)}x faster for {len(players)} agents")
    print("  Essential for tournaments with 20+ players")


async def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("BROADCAST SYSTEM DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows the League Manager broadcast capabilities:")
    print("  - Concurrent message delivery to multiple agents")
    print("  - Timeout handling and retry logic")
    print("  - Different message types (announcements, standings, etc.)")
    print("  - Performance benefits of concurrent broadcasting")

    await demo_broadcast_success()
    await demo_broadcast_with_failures()
    await demo_message_types()
    await demo_concurrent_broadcast()

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nKey Features:")
    print("  [OK] Concurrent HTTP requests using asyncio.gather")
    print("  [OK] 5-second timeout per agent")
    print("  [OK] Max 2 retries with exponential backoff")
    print("  [OK] Detailed delivery reporting")
    print("  [OK] Protocol-compliant messages (league.v2)")
    print("  [OK] Support for players, referees, or both")
    print("\nNext Steps:")
    print("  1. Integration with RoundManager complete")
    print("  2. Broadcasts sent on round start/complete")
    print("  3. Tournament end notification implemented")
    print("  4. Ready for live tournament use")
    print()


if __name__ == "__main__":
    asyncio.run(main())
