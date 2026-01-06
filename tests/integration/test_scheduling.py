"""
Integration Test: Round-Robin Scheduling (Task 29).

Tests the League Manager's round-robin scheduling algorithm.
"""

import pytest
from tests.integration.utils import MCPClient


@pytest.mark.asyncio
async def test_schedule_with_2_players(league_manager, two_players):
    """
    Test scheduling with 2 players.

    Expected:
        - 1 round generated
        - 1 match total (P1 vs P2)
        - Each player plays once
    """
    player1, player2 = two_players

    async with MCPClient() as client:
        # Register both players
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "sched-p1",
                "player_meta": {
                    "display_name": "Player1",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player1.endpoint
                }
            }
        )

        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:01Z",
                "conversation_id": "sched-p2",
                "player_meta": {
                    "display_name": "Player2",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player2.endpoint
                }
            }
        )

        # Start league (generate schedule)
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "test_league_2p",
                "game_type": "even_odd"
            }
        )

        schedule = response["result"]["schedule"]

        # Verify schedule structure
        assert "rounds" in schedule
        assert len(schedule["rounds"]) == 1  # 2 players = 1 round

        # Verify match count
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )
        assert total_matches == 1  # N*(N-1)/2 = 2*1/2 = 1


@pytest.mark.asyncio
async def test_schedule_with_3_players(league_manager, three_players):
    """
    Test scheduling with 3 players.

    Expected:
        - 3 rounds generated (odd N = N rounds)
        - 3 matches total (each pair plays once)
        - Each player plays 2 matches
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Register all players
        for idx, player in enumerate([player1, player2, player3], 1):
            await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"sched-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )

        # Start league
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "test_league_3p",
                "game_type": "even_odd"
            }
        )

        schedule = response["result"]["schedule"]

        # Verify rounds (3 players = 3 rounds for odd N)
        assert len(schedule["rounds"]) == 3

        # Verify total matches (N*(N-1)/2 = 3*2/2 = 3)
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )
        assert total_matches == 3


@pytest.mark.asyncio
async def test_schedule_with_4_players(league_manager, agent_manager, port_manager):
    """
    Test scheduling with 4 players.

    Expected:
        - 3 rounds (even N = N-1 rounds)
        - 6 matches total
        - Each player plays 3 matches
    """
    # Start 4 players
    players = []
    for i in range(4):
        port = port_manager.allocate()
        player = await agent_manager.start_player(f"P0{i+1}", port)
        players.append(player)

    async with MCPClient() as client:
        # Register all players
        for idx, player in enumerate(players, 1):
            await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"sched-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )

        # Start league
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "test_league_4p",
                "game_type": "even_odd"
            }
        )

        schedule = response["result"]["schedule"]

        # Verify rounds (4 players = 3 rounds for even N)
        assert len(schedule["rounds"]) == 3

        # Verify total matches (N*(N-1)/2 = 4*3/2 = 6)
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )
        assert total_matches == 6


@pytest.mark.asyncio
async def test_each_player_plays_once(league_manager, three_players):
    """
    Test that each pair of players plays exactly once.

    Expected:
        - No duplicate matchups
        - All possible pairs are scheduled
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
                    "conversation_id": f"sched-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        # Start league
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "test_league_unique",
                "game_type": "even_odd"
            }
        )

        schedule = response["result"]["schedule"]

        # Collect all matchups
        matchups = set()
        for round_data in schedule["rounds"]:
            for match in round_data["matches"]:
                p1 = match["player1_id"]
                p2 = match["player2_id"]
                # Store as sorted tuple for uniqueness
                matchup = tuple(sorted([p1, p2]))
                matchups.add(matchup)

        # Verify all unique pairs scheduled
        expected_pairs = {
            tuple(sorted([player_ids[0], player_ids[1]])),
            tuple(sorted([player_ids[0], player_ids[2]])),
            tuple(sorted([player_ids[1], player_ids[2]]))
        }

        assert matchups == expected_pairs


@pytest.mark.asyncio
async def test_no_concurrent_player_matches(league_manager, three_players):
    """
    Test that no player plays multiple matches in same round.

    Expected:
        - In each round, each player appears at most once
        - No scheduling conflicts
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        # Register players
        for idx, player in enumerate([player1, player2, player3], 1):
            await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"sched-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )

        # Start league
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "test_league_concurrent",
                "game_type": "even_odd"
            }
        )

        schedule = response["result"]["schedule"]

        # Check each round for conflicts
        for round_data in schedule["rounds"]:
            players_in_round = []
            for match in round_data["matches"]:
                players_in_round.append(match["player1_id"])
                players_in_round.append(match["player2_id"])

            # Each player should appear at most once per round
            assert len(players_in_round) == len(set(players_in_round))
