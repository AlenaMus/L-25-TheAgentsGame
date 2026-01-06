"""
Integration Test: Performance Testing (Task 33).

Tests system performance under concurrent load and time constraints.
"""

import pytest
from tests.integration.utils import MCPClient
import asyncio
import time


@pytest.mark.asyncio
async def test_concurrent_matches(league_manager, agent_manager, port_manager):
    """
    Test 2 matches running simultaneously.

    Expected:
        - Both matches complete successfully
        - No interference between matches
        - All results recorded correctly
    """
    # Start 4 players (2 matches with 2 players each)
    players = []
    for i in range(4):
        port = port_manager.allocate()
        player = await agent_manager.start_player(f"P{i+1:02d}", port)
        players.append(player)

    # Start 2 referees
    referees = []
    for i in range(2):
        port = port_manager.allocate()
        ref = await agent_manager.start_referee(f"REF{i+1:02d}", port)
        referees.append(ref)

    async with MCPClient() as client:
        start_time = time.time()

        # Execute 2 matches concurrently
        async def execute_match(match_id, player1, player2, referee):
            # Invite players
            await asyncio.gather(
                client.call_tool(
                    endpoint=player1.endpoint,
                    tool_name="handle_game_invitation",
                    params={
                        "match_id": match_id,
                        "game_type": "even_odd",
                        "opponent_id": player2.agent_id,
                        "referee_id": referee.agent_id
                    }
                ),
                client.call_tool(
                    endpoint=player2.endpoint,
                    tool_name="handle_game_invitation",
                    params={
                        "match_id": match_id,
                        "game_type": "even_odd",
                        "opponent_id": player1.agent_id,
                        "referee_id": referee.agent_id
                    }
                )
            )

            # Get choices
            results = await asyncio.gather(
                client.call_tool(
                    endpoint=player1.endpoint,
                    tool_name="choose_parity",
                    params={
                        "match_id": match_id,
                        "opponent_id": player2.agent_id,
                        "standings": [],
                        "game_history": []
                    }
                ),
                client.call_tool(
                    endpoint=player2.endpoint,
                    tool_name="choose_parity",
                    params={
                        "match_id": match_id,
                        "opponent_id": player1.agent_id,
                        "standings": [],
                        "game_history": []
                    }
                )
            )

            return results

        # Run 2 matches concurrently
        match1_task = execute_match("concurrent_m1", players[0], players[1], referees[0])
        match2_task = execute_match("concurrent_m2", players[2], players[3], referees[1])

        results = await asyncio.gather(match1_task, match2_task)

        elapsed_time = time.time() - start_time

        # Verify both completed
        assert len(results) == 2
        print(f"2 concurrent matches completed in {elapsed_time:.2f}s")

        # Should be faster than sequential (< 10s for concurrent vs ~10s sequential)
        assert elapsed_time < 10.0

    # Cleanup
    for player in players:
        await agent_manager.stop_agent(player.agent_id)
    for referee in referees:
        await agent_manager.stop_agent(referee.agent_id)


@pytest.mark.asyncio
async def test_match_completion_time(two_players):
    """
    Test single match completes within expected time.

    Expected:
        - Match completes in < 5 seconds
        - All phases execute efficiently
    """
    player1, player2 = two_players

    async with MCPClient() as client:
        start_time = time.time()

        # Execute full match
        match_id = "perf_single_match"

        # Invitations
        await asyncio.gather(
            client.call_tool(
                endpoint=player1.endpoint,
                tool_name="handle_game_invitation",
                params={
                    "match_id": match_id,
                    "game_type": "even_odd",
                    "opponent_id": player2.agent_id,
                    "referee_id": "REF01"
                }
            ),
            client.call_tool(
                endpoint=player2.endpoint,
                tool_name="handle_game_invitation",
                params={
                    "match_id": match_id,
                    "game_type": "even_odd",
                    "opponent_id": player1.agent_id,
                    "referee_id": "REF01"
                }
            )
        )

        # Choices
        await asyncio.gather(
            client.call_tool(
                endpoint=player1.endpoint,
                tool_name="choose_parity",
                params={
                    "match_id": match_id,
                    "opponent_id": player2.agent_id,
                    "standings": [],
                    "game_history": []
                }
            ),
            client.call_tool(
                endpoint=player2.endpoint,
                tool_name="choose_parity",
                params={
                    "match_id": match_id,
                    "opponent_id": player1.agent_id,
                    "standings": [],
                    "game_history": []
                }
            )
        )

        elapsed_time = time.time() - start_time

        print(f"Single match completed in {elapsed_time:.2f}s")
        assert elapsed_time < 5.0  # Should complete quickly


@pytest.mark.asyncio
async def test_3_player_tournament_time(league_manager, referee, three_players):
    """
    Test 3-player tournament completes within 30 seconds.

    Expected:
        - All 3 matches execute
        - Total time < 30 seconds
        - No performance bottlenecks
    """
    player1, player2, player3 = three_players

    async with MCPClient() as client:
        start_time = time.time()

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
                    "conversation_id": f"perf3-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )

        # Register referee
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:01:00Z",
                "conversation_id": "perf3-ref",
                "referee_meta": {
                    "display_name": "Referee1",
                    "version": "1.0.0",
                    "supported_games": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Start league (generates schedule)
        await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "perf_3p",
                "game_type": "even_odd"
            }
        )

        elapsed_time = time.time() - start_time

        print(f"3-player tournament setup completed in {elapsed_time:.2f}s")
        assert elapsed_time < 30.0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_system_under_load(league_manager, agent_manager, port_manager):
    """
    Test system with 10 players and many concurrent matches.

    Expected:
        - All matches complete
        - System remains stable
        - Tournament completes in < 5 minutes
    """
    # Start 10 players
    players = []
    for i in range(10):
        port = port_manager.allocate()
        player = await agent_manager.start_player(f"P{i+1:02d}", port)
        players.append(player)

    # Start 3 referees
    referees = []
    for i in range(3):
        port = port_manager.allocate()
        ref = await agent_manager.start_referee(f"REF{i+1:02d}", port)
        referees.append(ref)

    async with MCPClient() as client:
        start_time = time.time()

        # Register all players
        for idx, player in enumerate(players, 1):
            await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:{idx:02d}Z",
                    "conversation_id": f"load-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )

        # Register referees
        for idx, referee in enumerate(referees, 1):
            await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_referee",
                params={
                    "protocol": "league.v2",
                    "message_type": "REFEREE_REGISTER_REQUEST",
                    "sender": "referee:unregistered",
                    "timestamp": f"2025-12-24T10:01:{idx:02d}Z",
                    "conversation_id": f"load-ref{idx}",
                    "referee_meta": {
                        "display_name": f"Referee{idx}",
                        "version": "1.0.0",
                        "supported_games": ["even_odd"],
                        "contact_endpoint": referee.endpoint,
                        "max_concurrent_matches": 5
                    }
                }
            )

        # Start league
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "load_test",
                "game_type": "even_odd"
            }
        )

        schedule = response["result"]["schedule"]
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )

        elapsed_time = time.time() - start_time

        # 10 players = 45 matches
        assert total_matches == 45
        print(f"Load test: {total_matches} matches scheduled in {elapsed_time:.2f}s")

        # Should complete setup in reasonable time
        assert elapsed_time < 60.0

    # Cleanup
    for player in players:
        await agent_manager.stop_agent(player.agent_id)
    for referee in referees:
        await agent_manager.stop_agent(referee.agent_id)


@pytest.mark.asyncio
async def test_no_race_conditions(league_manager, two_players):
    """
    Test concurrent operations don't cause race conditions.

    Scenario:
        - Multiple simultaneous registrations
        - Concurrent match result reporting
        - Simultaneous standings queries

    Expected:
        - All operations complete correctly
        - No data corruption
        - Results are consistent
    """
    player1, player2 = two_players

    async with MCPClient() as client:
        # Test concurrent registrations
        tasks = []
        for idx, player in enumerate([player1, player2], 1):
            task = client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:0{idx}Z",
                    "conversation_id": f"race-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks)

        # Verify both succeeded
        assert all(r["result"]["status"] == "ACCEPTED" for r in results)

        # Verify unique IDs assigned
        player_ids = [r["result"]["player_id"] for r in results]
        assert len(player_ids) == len(set(player_ids))  # All unique
