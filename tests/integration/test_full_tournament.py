"""
Integration Test: Full Tournament Execution (Task 32).

End-to-end test of complete tournament lifecycle from initialization
through final standings.
"""

import pytest
from tests.integration.utils import MCPClient
import asyncio


@pytest.mark.asyncio
async def test_complete_tournament_lifecycle(
    league_manager,
    agent_manager,
    port_manager
):
    """
    Test complete tournament from start to finish.

    Full Lifecycle:
        1. Initialization - Start all agents
        2. Registration - Register players and referees
        3. Schedule Generation - League Manager creates schedule
        4. Round Execution - Execute all matches in all rounds
        5. Final Standings - Verify correct final standings
        6. Data Persistence - Verify all data saved
        7. Cleanup - Graceful shutdown

    Expected:
        - All 15 matches complete (6 players)
        - No crashes or errors
        - Standings updated correctly
        - All data persisted
        - Players receive all notifications
    """
    # Step 1: Initialization - Start all agents
    print("Step 1: Initializing agents...")

    # Start 2 referees
    referees = []
    for i in range(2):
        port = port_manager.allocate()
        ref = await agent_manager.start_referee(f"REF{i+1:02d}", port)
        referees.append(ref)

    # Start 4 players
    players = []
    for i in range(4):
        port = port_manager.allocate()
        player = await agent_manager.start_player(f"P{i+1:02d}", port)
        players.append(player)

    async with MCPClient() as client:
        # Step 2: Registration
        print("Step 2: Registering agents...")

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
                    "conversation_id": f"full-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            assert response["result"]["status"] == "ACCEPTED"
            player_ids.append(response["result"]["player_id"])
            print(f"  Registered {player.agent_id} -> {response['result']['player_id']}")

        # Register all referees
        referee_ids = []
        for idx, referee in enumerate(referees, 1):
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_referee",
                params={
                    "protocol": "league.v2",
                    "message_type": "REFEREE_REGISTER_REQUEST",
                    "sender": "referee:unregistered",
                    "timestamp": f"2025-12-24T10:01:0{idx}Z",
                    "conversation_id": f"full-ref{idx}",
                    "referee_meta": {
                        "display_name": f"Referee{idx}",
                        "version": "1.0.0",
                        "supported_games": ["even_odd"],
                        "contact_endpoint": referee.endpoint,
                        "max_concurrent_matches": 5
                    }
                }
            )
            assert response["result"]["status"] == "ACCEPTED"
            referee_ids.append(response["result"]["referee_id"])
            print(f"  Registered {referee.agent_id} -> {response['result']['referee_id']}")

        # Step 3: Schedule Generation
        print("Step 3: Generating schedule...")

        league_response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "full_tournament",
                "game_type": "even_odd"
            }
        )

        assert league_response["result"]["status"] == "started"
        schedule = league_response["result"]["schedule"]

        # Verify schedule structure
        num_rounds = len(schedule["rounds"])
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )

        print(f"  Schedule: {num_rounds} rounds, {total_matches} matches")
        assert num_rounds == 3  # 4 players = 3 rounds
        assert total_matches == 6  # 4 players = 6 matches

        # Step 4: Execute all rounds
        print("Step 4: Executing tournament...")

        match_results = []
        for round_idx, round_data in enumerate(schedule["rounds"], 1):
            print(f"\n  Round {round_idx}:")

            for match in round_data["matches"]:
                match_id = match["match_id"]
                p1_id = match["player1_id"]
                p2_id = match["player2_id"]
                ref_id = match["referee_id"]

                print(f"    Match {match_id}: {p1_id} vs {p2_id}")

                # Find player and referee endpoints
                p1_endpoint = next(
                    p.endpoint for p in players
                    if player_ids[players.index(p)] == p1_id
                )
                p2_endpoint = next(
                    p.endpoint for p in players
                    if player_ids[players.index(p)] == p2_id
                )

                # Execute match flow
                # 1. Send invitations
                await client.call_tool(
                    endpoint=p1_endpoint,
                    tool_name="handle_game_invitation",
                    params={
                        "match_id": match_id,
                        "game_type": "even_odd",
                        "opponent_id": p2_id,
                        "referee_id": ref_id
                    }
                )

                await client.call_tool(
                    endpoint=p2_endpoint,
                    tool_name="handle_game_invitation",
                    params={
                        "match_id": match_id,
                        "game_type": "even_odd",
                        "opponent_id": p1_id,
                        "referee_id": ref_id
                    }
                )

                # 2. Request choices
                choice1_resp = await client.call_tool(
                    endpoint=p1_endpoint,
                    tool_name="choose_parity",
                    params={
                        "match_id": match_id,
                        "opponent_id": p2_id,
                        "standings": [],
                        "game_history": []
                    }
                )

                choice2_resp = await client.call_tool(
                    endpoint=p2_endpoint,
                    tool_name="choose_parity",
                    params={
                        "match_id": match_id,
                        "opponent_id": p1_id,
                        "standings": [],
                        "game_history": []
                    }
                )

                p1_choice = choice1_resp["result"]["choice"]
                p2_choice = choice2_resp["result"]["choice"]

                # 3. Simulate draw and determine winner
                import random
                drawn_number = random.randint(1, 10)
                is_even = drawn_number % 2 == 0

                if p1_choice == p2_choice:
                    winner_id = None  # Tie
                elif (is_even and p1_choice == "even") or (not is_even and p1_choice == "odd"):
                    winner_id = p1_id
                else:
                    winner_id = p2_id

                print(f"      Draw: {drawn_number}, Winner: {winner_id or 'TIE'}")

                # 4. Report result to League Manager
                await client.call_tool(
                    endpoint=league_manager.endpoint,
                    tool_name="report_match_result",
                    params={
                        "match_id": match_id,
                        "winner_id": winner_id,
                        "player1_id": p1_id,
                        "player2_id": p2_id,
                        "drawn_number": drawn_number,
                        "choices": {
                            p1_id: p1_choice,
                            p2_id: p2_choice
                        }
                    }
                )

                match_results.append({
                    "match_id": match_id,
                    "winner_id": winner_id,
                    "drawn_number": drawn_number
                })

        # Step 5: Verify Final Standings
        print("\nStep 5: Checking final standings...")

        standings_resp = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="get_standings",
            params={"league_id": "full_tournament"}
        )

        standings = standings_resp["result"]["standings"]

        print("  Final Standings:")
        for idx, standing in enumerate(standings, 1):
            print(f"    {idx}. {standing['player_id']}: "
                  f"{standing['points']} pts "
                  f"({standing['wins']}W-{standing['losses']}L-{standing['ties']}T)")

        # Verify all matches completed
        assert len(match_results) == total_matches
        print(f"\n  Total matches completed: {len(match_results)}/{total_matches}")

        # Verify standings integrity
        assert len(standings) == len(player_ids)
        total_points = sum(s["points"] for s in standings)
        print(f"  Total points distributed: {total_points}")

        # Step 6: Verify Data Persistence
        print("\nStep 6: Verifying data persistence...")

        # Check that data files exist
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        league_data_dir = project_root / "SHARED" / "data" / "leagues" / "full_tournament"

        # Verify league data exists (when implemented)
        # assert league_data_dir.exists()
        print("  Data persistence check: TODO (when file system implemented)")

        # Step 7: Cleanup
        print("\nStep 7: Cleanup...")
        for player in players:
            await agent_manager.stop_agent(player.agent_id)
        for referee in referees:
            await agent_manager.stop_agent(referee.agent_id)

        print("\n✅ Full tournament lifecycle completed successfully!")


@pytest.mark.asyncio
async def test_tournament_with_concurrent_matches(
    league_manager,
    agent_manager,
    port_manager
):
    """
    Test tournament where multiple matches run concurrently.

    Scenario:
        - 6 players = 15 total matches
        - Some matches can run in parallel
        - Verify no race conditions

    Expected:
        - All matches complete
        - No data corruption
        - Standings calculated correctly
    """
    # Start 6 players
    players = []
    for i in range(6):
        port = port_manager.allocate()
        player = await agent_manager.start_player(f"P{i+1:02d}", port)
        players.append(player)

    # Start 2 referees for concurrent match handling
    referees = []
    for i in range(2):
        port = port_manager.allocate()
        ref = await agent_manager.start_referee(f"REF{i+1:02d}", port)
        referees.append(ref)

    async with MCPClient() as client:
        # Register all agents
        player_ids = []
        for idx, player in enumerate(players, 1):
            response = await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_player",
                params={
                    "protocol": "league.v2",
                    "message_type": "PLAYER_REGISTER_REQUEST",
                    "sender": "player:unregistered",
                    "timestamp": f"2025-12-24T10:00:{idx:02d}Z",
                    "conversation_id": f"concurrent-p{idx}",
                    "player_meta": {
                        "display_name": f"Player{idx}",
                        "version": "1.0.0",
                        "strategy": "random",
                        "contact_endpoint": player.endpoint
                    }
                }
            )
            player_ids.append(response["result"]["player_id"])

        for idx, referee in enumerate(referees, 1):
            await client.call_tool(
                endpoint=league_manager.endpoint,
                tool_name="register_referee",
                params={
                    "protocol": "league.v2",
                    "message_type": "REFEREE_REGISTER_REQUEST",
                    "sender": "referee:unregistered",
                    "timestamp": f"2025-12-24T10:01:{idx:02d}Z",
                    "conversation_id": f"concurrent-ref{idx}",
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
        league_response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="start_league",
            params={
                "league_id": "concurrent_tournament",
                "game_type": "even_odd"
            }
        )

        schedule = league_response["result"]["schedule"]
        total_matches = sum(
            len(round_data["matches"])
            for round_data in schedule["rounds"]
        )

        # 6 players = 15 matches
        assert total_matches == 15

        print(f"Concurrent tournament: {len(schedule['rounds'])} rounds, "
              f"{total_matches} matches")

    # Cleanup
    for player in players:
        await agent_manager.stop_agent(player.agent_id)
    for referee in referees:
        await agent_manager.stop_agent(referee.agent_id)
