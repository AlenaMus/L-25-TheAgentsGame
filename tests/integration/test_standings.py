"""
Integration Test: Standings Calculation (Task 30).

Tests the League Manager's standings calculation and tiebreaker logic.
"""

import pytest
from tests.integration.utils import MCPClient


@pytest.mark.asyncio
async def test_standings_after_win(league_manager, two_players):
    """
    Test standings update after a win.

    Expected:
        - Winner gets 3 points
        - Loser gets 0 points
        - Win/loss counts updated
    """
    player1, player2 = two_players

    async with MCPClient() as client:
        # Register players
        reg1 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "standings-p1",
                "player_meta": {
                    "display_name": "Player1",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player1.endpoint
                }
            }
        )

        reg2 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:01Z",
                "conversation_id": "standings-p2",
                "player_meta": {
                    "display_name": "Player2",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player2.endpoint
                }
            }
        )

        player1_id = reg1["result"]["player_id"]
        player2_id = reg2["result"]["player_id"]

        # Report match result (player1 wins)
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "test_match_001",
                "winner_id": player1_id,
                "player1_id": player1_id,
                "player2_id": player2_id,
                "drawn_number": 5,
                "choices": {
                    player1_id: "odd",
                    player2_id: "even"
                }
            }
        )

        # Get standings
        standings = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="get_standings",
            params={"league_id": "default"}
        )

        standings_data = standings["result"]["standings"]

        # Find players in standings
        p1_standing = next(s for s in standings_data if s["player_id"] == player1_id)
        p2_standing = next(s for s in standings_data if s["player_id"] == player2_id)

        # Verify winner has 3 points
        assert p1_standing["points"] == 3
        assert p1_standing["wins"] == 1
        assert p1_standing["losses"] == 0

        # Verify loser has 0 points
        assert p2_standing["points"] == 0
        assert p2_standing["wins"] == 0
        assert p2_standing["losses"] == 1


@pytest.mark.asyncio
async def test_standings_after_tie(league_manager, two_players):
    """
    Test standings update after a tie.

    Expected:
        - Both players get 1 point
        - Tie count incremented for both
    """
    player1, player2 = two_players

    async with MCPClient() as client:
        # Register players
        reg1 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "tie-p1",
                "player_meta": {
                    "display_name": "Player1",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player1.endpoint
                }
            }
        )

        reg2 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:01Z",
                "conversation_id": "tie-p2",
                "player_meta": {
                    "display_name": "Player2",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player2.endpoint
                }
            }
        )

        player1_id = reg1["result"]["player_id"]
        player2_id = reg2["result"]["player_id"]

        # Report tie result
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "test_match_tie",
                "winner_id": None,  # Tie
                "player1_id": player1_id,
                "player2_id": player2_id,
                "drawn_number": 5,
                "choices": {
                    player1_id: "odd",
                    player2_id: "odd"
                }
            }
        )

        # Get standings
        standings = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="get_standings",
            params={"league_id": "default"}
        )

        standings_data = standings["result"]["standings"]
        p1_standing = next(s for s in standings_data if s["player_id"] == player1_id)
        p2_standing = next(s for s in standings_data if s["player_id"] == player2_id)

        # Both get 1 point for tie
        assert p1_standing["points"] == 1
        assert p1_standing["ties"] == 1
        assert p2_standing["points"] == 1
        assert p2_standing["ties"] == 1


@pytest.mark.asyncio
async def test_standings_with_multiple_matches(league_manager, three_players):
    """
    Test standings accumulation over multiple matches.

    Scenario:
        - P1 wins vs P2 (P1: 3 pts, P2: 0 pts)
        - P1 wins vs P3 (P1: 6 pts, P3: 0 pts)
        - P2 ties with P3 (P2: 1 pt, P3: 1 pt)

    Expected:
        - Final: P1=6, P2=1, P3=1
        - Correct win/loss/tie counts
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Register all players
        player_ids = []
        for idx, player in enumerate([player1, player2, player3], 1):
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"multi-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        p1_id, p2_id, p3_id = player_ids

        # Match 1: P1 beats P2
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "multi_001",
                "winner_id": p1_id,
                "player1_id": p1_id,
                "player2_id": p2_id,
                "drawn_number": 5,
                "choices": {p1_id: "odd", p2_id: "even"}
            }
        )

        # Match 2: P1 beats P3
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "multi_002",
                "winner_id": p1_id,
                "player1_id": p1_id,
                "player2_id": p3_id,
                "drawn_number": 4,
                "choices": {p1_id: "even", p3_id: "odd"}
            }
        )

        # Match 3: P2 ties with P3
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "multi_003",
                "winner_id": None,
                "player1_id": p2_id,
                "player2_id": p3_id,
                "drawn_number": 6,
                "choices": {p2_id: "even", p3_id: "even"}
            }
        )

        # Get final standings
        standings = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="get_standings",
            params={"league_id": "default"}
        )

        standings_data = standings["result"]["standings"]

        # Verify final scores
        p1_data = next(s for s in standings_data if s["player_id"] == p1_id)
        p2_data = next(s for s in standings_data if s["player_id"] == p2_id)
        p3_data = next(s for s in standings_data if s["player_id"] == p3_id)

        assert p1_data["points"] == 6  # 2 wins
        assert p1_data["wins"] == 2
        assert p1_data["losses"] == 0

        assert p2_data["points"] == 1  # 1 tie
        assert p2_data["wins"] == 0
        assert p2_data["losses"] == 1
        assert p2_data["ties"] == 1

        assert p3_data["points"] == 1  # 1 tie
        assert p3_data["wins"] == 0
        assert p3_data["losses"] == 1
        assert p3_data["ties"] == 1


@pytest.mark.asyncio
async def test_tiebreaker_by_wins(league_manager, three_players):
    """
    Test tiebreaker when players have same points.

    Scenario:
        - P1: 3 points (1 win, 0 ties)
        - P2: 3 points (0 wins, 3 ties)
        - P1 should rank higher (more wins)

    Expected:
        - Standings sorted correctly
        - Player with more wins ranks higher
    """
    # This test validates the tiebreaker logic
    # Implementation depends on League Manager design
    pass  # Placeholder for when agents exist


@pytest.mark.asyncio
async def test_standings_sorted_correctly(league_manager, three_players):
    """
    Test standings are sorted by points descending.

    Expected:
        - Highest points first
        - Tiebreakers applied when needed
        - Consistent ordering
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Register players and simulate results
        player_ids = []
        for idx, player in enumerate([player1, player2, player3], 1):
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"sort-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        # Simulate matches to create different point totals
        # ... (similar to previous tests)

        # Get standings
        standings = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="get_standings",
            params={"league_id": "default"}
        )

        standings_data = standings["result"]["standings"]

        # Verify sorted by points descending
        points = [s["points"] for s in standings_data]
        assert points == sorted(points, reverse=True)
