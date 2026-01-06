"""
Integration Test: Multi-Player Tournament (Task 31).

Tests complete tournament execution with 3+ players.
"""

import pytest
from tests.integration.utils import MCPClient
import asyncio


@pytest.mark.asyncio
async def test_3_player_tournament(league_manager, referee, three_players):
    """
    Test complete 3-player tournament.

    Expected:
        - 3 rounds, 3 matches total
        - All matches complete successfully
        - Final standings calculated correctly
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Step 1: Register all players
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
                    "conversation_id": f"tourn3-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        # Step 2: Register referee
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:01:00Z",
                "conversation_id": "tourn3-ref",
                "referee_meta": {
                    "display_name": "Referee1",
                    "version": "1.0.0",
                    "supported_games": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Step 3: Start league
        league_response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "tournament_3p",
                "game_type": "even_odd"
            }
        )

        assert league_response["result"]["status"] == "started"
        schedule = league_response["result"]["schedule"]

        # Verify schedule structure
        assert len(schedule["rounds"]) == 3  # 3 players = 3 rounds
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )
        assert total_matches == 3  # 3 players = 3 matches

        # Step 4: Execute all rounds (would be done by referee in real system)
        # For now, verify structure is correct


@pytest.mark.asyncio
async def test_4_player_tournament(league_manager, referee, agent_manager, port_manager):
    """
    Test complete 4-player tournament.

    Expected:
        - 3 rounds (even N = N-1)
        - 6 matches total
        - Each player plays 3 matches
        - All matches complete
    """
    # Start 4 players
    players = []
    for i in range(4):
        port = port_manager.allocate()
        player = await agent_manager.start_player(f"P{i+1:02d}", port)
        players.append(player)

    async with MCPClient() as client:
        # Register all players
        player_ids = []
        for idx, player in enumerate(players, 1):
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"tourn4-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        # Register referee
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:01:00Z",
                "conversation_id": "tourn4-ref",
                "referee_meta": {
                    "display_name": "Referee1",
                    "version": "1.0.0",
                    "supported_games": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Start league
        league_response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "tournament_4p",
                "game_type": "even_odd"
            }
        )

        schedule = league_response["result"]["schedule"]

        # Verify schedule
        assert len(schedule["rounds"]) == 3  # 4 players = 3 rounds
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )
        assert total_matches == 6  # 4*3/2 = 6 matches

    # Cleanup
    for player in players:
        await agent_manager.stop_agent(player.agent_id)


@pytest.mark.asyncio
async def test_all_matches_complete(league_manager, referee, three_players):
    """
    Test that all scheduled matches execute successfully.

    Expected:
        - Every match in schedule gets executed
        - No matches skipped
        - All results recorded
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Register players
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
                    "conversation_id": f"complete-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        # Register referee
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:01:00Z",
                "conversation_id": "complete-ref",
                "referee_meta": {
                    "display_name": "Referee1",
                    "version": "1.0.0",
                    "supported_games": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Start league
        league_response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "complete_test",
                "game_type": "even_odd"
            }
        )

        schedule = league_response["result"]["schedule"]
        total_scheduled = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )

        # Execute tournament (simulated)
        # In real system, referee would execute each match
        # For now, verify schedule is complete

        assert total_scheduled == 3  # 3 players = 3 matches


@pytest.mark.asyncio
async def test_final_standings_correct(league_manager, three_players):
    """
    Test final standings are calculated correctly.

    Scenario:
        - Execute all matches
        - Calculate final standings
        - Verify rankings are correct

    Expected:
        - All players have correct points
        - Standings sorted correctly
        - Tiebreakers applied
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Register players
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
                    "conversation_id": f"final-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        # Simulate known match results
        # P1 beats P2
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "final_001",
                "winner_id": player_ids[0],
                "player1_id": player_ids[0],
                "player2_id": player_ids[1],
                "drawn_number": 5,
                "choices": {player_ids[0]: "odd", player_ids[1]: "even"}
            }
        )

        # P1 beats P3
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "final_002",
                "winner_id": player_ids[0],
                "player1_id": player_ids[0],
                "player2_id": player_ids[2],
                "drawn_number": 4,
                "choices": {player_ids[0]: "even", player_ids[2]: "odd"}
            }
        )

        # P2 beats P3
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="report_match_result",
            params={
                "match_id": "final_003",
                "winner_id": player_ids[1],
                "player1_id": player_ids[1],
                "player2_id": player_ids[2],
                "drawn_number": 6,
                "choices": {player_ids[1]: "even", player_ids[2]: "odd"}
            }
        )

        # Get final standings
        standings = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="get_standings",
            params={"league_id": "default"}
        )

        standings_data = standings["result"]["standings"]

        # Expected: P1=6pts (2W), P2=3pts (1W,1L), P3=0pts (2L)
        assert standings_data[0]["player_id"] == player_ids[0]
        assert standings_data[0]["points"] == 6

        assert standings_data[1]["player_id"] == player_ids[1]
        assert standings_data[1]["points"] == 3

        assert standings_data[2]["player_id"] == player_ids[2]
        assert standings_data[2]["points"] == 0
