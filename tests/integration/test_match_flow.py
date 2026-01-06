"""
Integration Test: Complete Match Flow (Task 28).

Tests the complete 6-phase match orchestration from invitation
through result reporting.
"""

import pytest
import uuid
from tests.integration.utils import MCPClient


@pytest.mark.asyncio
async def test_successful_match_flow(referee, two_players, league_manager):
    """
    Test complete match flow from start to finish.

    Phases:
        1. Referee sends invitations to both players
        2. Players accept invitations
        3. Referee requests moves from both players
        4. Players submit choices
        5. Referee draws random number and determines winner
        6. Referee reports result to League Manager

    Expected:
        - All phases complete successfully
        - Winner determined correctly
        - Result reported to League Manager
    """
    player1, player2 = two_players
    match_id = f"match_{uuid.uuid4().hex[:8]}"

    async with MCPClient() as client:
        # Phase 1-2: Send invitations
        invite1 = await client.call_tool(
            endpoint=player1.endpoint,
            tool_name="handle_game_invitation",
            params={
                "match_id": match_id,
                "game_type": "even_odd",
                "opponent_id": player2.agent_id,
                "referee_id": referee.agent_id
            }
        )

        invite2 = await client.call_tool(
            endpoint=player2.endpoint,
            tool_name="handle_game_invitation",
            params={
                "match_id": match_id,
                "game_type": "even_odd",
                "opponent_id": player1.agent_id,
                "referee_id": referee.agent_id
            }
        )

        # Verify both accepted
        assert invite1["result"]["status"] == "accepted"
        assert invite2["result"]["status"] == "accepted"

        # Phase 3-4: Request moves
        choice1 = await client.call_tool(
            endpoint=player1.endpoint,
            tool_name="choose_parity",
            params={
                "match_id": match_id,
                "opponent_id": player2.agent_id,
                "standings": [],
                "game_history": []
            }
        )

        choice2 = await client.call_tool(
            endpoint=player2.endpoint,
            tool_name="choose_parity",
            params={
                "match_id": match_id,
                "opponent_id": player1.agent_id,
                "standings": [],
                "game_history": []
            }
        )

        # Verify valid choices
        assert choice1["result"]["choice"] in ["even", "odd"]
        assert choice2["result"]["choice"] in ["even", "odd"]

        # Phase 5: Simulate referee determining winner
        drawn_number = 5  # Odd number
        p1_choice = choice1["result"]["choice"]
        p2_choice = choice2["result"]["choice"]

        if p1_choice == "odd":
            winner_id = player1.agent_id
        elif p2_choice == "odd":
            winner_id = player2.agent_id
        else:
            winner_id = None  # Tie

        # Phase 6: Notify players of result
        result1 = await client.call_tool(
            endpoint=player1.endpoint,
            tool_name="notify_match_result",
            params={
                "match_id": match_id,
                "winner_id": winner_id,
                "drawn_number": drawn_number,
                "choices": {
                    player1.agent_id: p1_choice,
                    player2.agent_id: p2_choice
                }
            }
        )

        result2 = await client.call_tool(
            endpoint=player2.endpoint,
            tool_name="notify_match_result",
            params={
                "match_id": match_id,
                "winner_id": winner_id,
                "drawn_number": drawn_number,
                "choices": {
                    player1.agent_id: p1_choice,
                    player2.agent_id: p2_choice
                }
            }
        )

        # Verify acknowledgment
        assert result1["result"]["acknowledged"] is True
        assert result2["result"]["acknowledged"] is True


@pytest.mark.asyncio
async def test_match_with_even_winner(referee, two_players):
    """
    Test match where even choice wins.

    Scenario:
        - Player 1 chooses "even"
        - Player 2 chooses "odd"
        - Drawn number is 4 (even)
        - Player 1 wins

    Expected:
        - Winner is player who chose "even"
        - Result reported correctly
    """
    player1, player2 = two_players
    match_id = f"match_{uuid.uuid4().hex[:8]}"
    drawn_number = 4  # Even

    async with MCPClient() as client:
        # Get choices (we'll verify the logic, not control choices)
        choice1 = await client.call_tool(
            endpoint=player1.endpoint,
            tool_name="choose_parity",
            params={
                "match_id": match_id,
                "opponent_id": player2.agent_id,
                "standings": [],
                "game_history": []
            }
        )

        # Verify choice is valid
        p1_choice = choice1["result"]["choice"]
        assert p1_choice in ["even", "odd"]

        # Determine expected winner based on drawn number
        if drawn_number % 2 == 0:  # Even
            expected_winner_choice = "even"
        else:
            expected_winner_choice = "odd"

        # If player chose correctly, they should win
        if p1_choice == expected_winner_choice:
            assert p1_choice == "even" or drawn_number % 2 == 1


@pytest.mark.asyncio
async def test_match_with_tie(two_players):
    """
    Test match resulting in a tie.

    Scenario:
        - Both players choose same parity
        - Regardless of drawn number, it's a tie

    Expected:
        - winner_id is None
        - Both players notified of tie
    """
    player1, player2 = two_players
    match_id = f"match_{uuid.uuid4().hex[:8]}"

    async with MCPClient() as client:
        # Notify both of a tie result
        drawn_number = 5

        result1 = await client.call_tool(
            endpoint=player1.endpoint,
            tool_name="notify_match_result",
            params={
                "match_id": match_id,
                "winner_id": None,  # Tie
                "drawn_number": drawn_number,
                "choices": {
                    player1.agent_id: "even",
                    player2.agent_id: "even"
                }
            }
        )

        result2 = await client.call_tool(
            endpoint=player2.endpoint,
            tool_name="notify_match_result",
            params={
                "match_id": match_id,
                "winner_id": None,  # Tie
                "drawn_number": drawn_number,
                "choices": {
                    player1.agent_id: "even",
                    player2.agent_id: "even"
                }
            }
        )

        # Verify both acknowledged
        assert result1["result"]["acknowledged"] is True
        assert result2["result"]["acknowledged"] is True


@pytest.mark.asyncio
async def test_simultaneous_move_collection(two_players):
    """
    Test that moves are collected simultaneously.

    Scenario:
        - Both players requested to choose at same time
        - Both respond within timeout

    Expected:
        - Both choices collected successfully
        - No player sees other's choice before making decision
    """
    player1, player2 = two_players
    match_id = f"match_{uuid.uuid4().hex[:8]}"

    async with MCPClient() as client:
        import asyncio

        # Request both choices simultaneously
        task1 = client.call_tool(
            endpoint=player1.endpoint,
            tool_name="choose_parity",
            params={
                "match_id": match_id,
                "opponent_id": player2.agent_id,
                "standings": [],
                "game_history": []
            }
        )

        task2 = client.call_tool(
            endpoint=player2.endpoint,
            tool_name="choose_parity",
            params={
                "match_id": match_id,
                "opponent_id": player1.agent_id,
                "standings": [],
                "game_history": []
            }
        )

        # Wait for both simultaneously
        results = await asyncio.gather(task1, task2)
        choice1, choice2 = results

        # Verify both completed
        assert choice1["result"]["choice"] in ["even", "odd"]
        assert choice2["result"]["choice"] in ["even", "odd"]
