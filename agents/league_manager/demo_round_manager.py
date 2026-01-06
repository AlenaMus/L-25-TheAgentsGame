#!/usr/bin/env python3
"""
Demonstration of Round Manager functionality.

Shows complete tournament flow:
1. Initialize tournament with schedule
2. Start first round and broadcast announcement
3. Receive match results and update standings
4. Complete round and announce completion
5. Progress through all rounds
6. Declare tournament complete
"""

import asyncio
import json
from league_manager.handlers import (
    RoundManager,
    RoundStatus,
    handle_match_result_report
)
from league_manager.standings import StandingsCalculator
from league_manager.scheduler import MatchScheduler


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_json(data: dict, title: str = None):
    """Pretty print JSON data."""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2))


async def main():
    """Run round manager demonstration."""
    print_section("ROUND MANAGER DEMONSTRATION")

    # Setup: Create 4 players
    print("Setting up tournament with 4 players...")
    player_ids = ["P01", "P02", "P03", "P04"]
    player_names = ["Alice", "Bob", "Charlie", "Diana"]

    # Create standings calculator and add players
    standings_calc = StandingsCalculator()
    for pid, name in zip(player_ids, player_names):
        standings_calc.add_player(pid, name)
        print(f"  OK {name} ({pid}) registered")

    # Create tournament schedule
    print("\nCreating tournament schedule...")
    scheduler = MatchScheduler()
    referees = [{"referee_id": "REF01"}]
    tournament_schedule = scheduler.create_tournament_schedule(
        player_ids, referees
    )

    print(f"  OK Schedule created: {len(tournament_schedule)} rounds")
    for round_idx, matches in enumerate(tournament_schedule):
        print(f"    Round {round_idx + 1}: {len(matches)} matches")
        for match in matches:
            print(f"      - {match.match_id}: {match.player_a_id} vs "
                  f"{match.player_b_id}")

    # Initialize round manager
    print("\nInitializing Round Manager...")
    round_manager = RoundManager(standings_calc, "league_2025_even_odd")
    round_manager.initialize_tournament(tournament_schedule)
    print(f"  OK Tournament initialized with {round_manager.total_rounds} rounds")

    # Simulate tournament rounds
    for round_num in range(1, round_manager.total_rounds + 1):
        print_section(f"ROUND {round_num}")

        # Start round
        print("Starting round and creating announcement...")
        announcement = round_manager.start_round(round_num)
        print_json(announcement, "ROUND_ANNOUNCEMENT Message")

        print(f"\n  Status: {round_manager.round_status[round_num].value}")
        print(f"  Matches in round: {len(announcement['matches'])}")

        # Simulate match results
        print("\nSimulating match results...")
        matches = round_manager.round_matches[round_num]

        for idx, match in enumerate(matches):
            print(f"\n  Match {idx + 1}/{len(matches)}: {match.match_id}")
            print(f"    {match.player_a_id} vs {match.player_b_id}")

            # Simulate winner (alternating for demonstration)
            winner = match.player_a_id if idx % 2 == 0 else match.player_b_id
            print(f"    Winner: {winner}")

            # Create match result report
            result_params = {
                "protocol": "league.v2",
                "message_type": "MATCH_RESULT_REPORT",
                "match_id": match.match_id,
                "round_id": round_num,
                "result": {
                    "winner": winner,
                    "score": {
                        match.player_a_id: 3 if winner == match.player_a_id else 0,
                        match.player_b_id: 3 if winner == match.player_b_id else 0
                    }
                }
            }

            # Handle result
            response = await handle_match_result_report(
                result_params,
                standings_calc,
                round_manager,
                "league_2025_even_odd"
            )

            print(f"    OK Result acknowledged: {response['acknowledged']}")
            print(f"    Round complete: {response['round_complete']}")

        # Complete round
        print("\n  All matches complete. Completing round...")
        completion_msg = round_manager.complete_round(round_num)
        print_json(completion_msg, "ROUND_COMPLETED Message")

        # Show current standings
        print("\n  Current Standings:")
        standings = standings_calc.get_standings()
        print(f"    {'Rank':<6} {'Player':<15} {'W':<3} {'L':<3} {'T':<3} {'Points':<7}")
        print(f"    {'-' * 45}")
        for standing in standings:
            print(f"    {standing.rank:<6} "
                  f"{standing.display_name:<15} "
                  f"{standing.wins:<3} "
                  f"{standing.losses:<3} "
                  f"{standing.ties:<3} "
                  f"{standing.points:<7}")

    # Tournament complete
    print_section("TOURNAMENT COMPLETE")
    print(f"  Tournament complete: {round_manager.is_tournament_complete()}")

    # Final standings
    print("\n  FINAL STANDINGS:")
    final_standings = standings_calc.get_standings()
    print(f"    {'Rank':<6} {'Player':<15} {'W':<3} {'L':<3} {'T':<3} {'Points':<7}")
    print(f"    {'-' * 45}")
    for standing in final_standings:
        print(f"    {standing.rank:<6} "
              f"{standing.display_name:<15} "
              f"{standing.wins:<3} "
              f"{standing.losses:<3} "
              f"{standing.ties:<3} "
              f"{standing.points:<7}")

    champion = final_standings[0]
    print(f"\n  🏆 CHAMPION: {champion.display_name} ({champion.player_id})")
    print(f"     Record: {champion.wins}W-{champion.losses}L-{champion.ties}T")
    print(f"     Points: {champion.points}")

    print_section("DEMONSTRATION COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
