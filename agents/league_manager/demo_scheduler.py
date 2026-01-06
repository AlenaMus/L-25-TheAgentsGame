#!/usr/bin/env python
"""
Demonstration of round-robin scheduler.

Shows scheduling for different player counts and referee assignments.
"""

import sys
sys.path.insert(0, 'src')

from league_manager.scheduler import (
    MatchScheduler,
    generate_round_robin_schedule,
    get_schedule_stats,
    validate_schedule
)


def demo_basic_schedule():
    """Demonstrate basic round-robin schedule generation."""
    print("=" * 70)
    print("DEMO 1: Basic Round-Robin Schedule (4 Players)")
    print("=" * 70)

    players = ["P01", "P02", "P03", "P04"]
    schedule = generate_round_robin_schedule(players)

    print(f"\nPlayers: {players}")
    print(f"Total players: {len(players)}")

    for round_idx, round_matches in enumerate(schedule):
        print(f"\nRound {round_idx + 1}:")
        for match in round_matches:
            print(f"  {match[0]} vs {match[1]}")

    stats = get_schedule_stats(schedule)
    print(f"\nStatistics:")
    print(f"  Total rounds: {stats['total_rounds']}")
    print(f"  Total matches: {stats['total_matches']}")
    print(f"  Matches per round: {stats['matches_per_round']}")
    print(f"  Avg matches/round: {stats['avg_matches_per_round']:.1f}")

    is_valid = validate_schedule(players, schedule)
    print(f"\nSchedule valid: {is_valid}")


def demo_odd_players():
    """Demonstrate schedule with odd number of players (byes)."""
    print("\n" + "=" * 70)
    print("DEMO 2: Schedule with Odd Players (5 Players, Byes)")
    print("=" * 70)

    players = ["P01", "P02", "P03", "P04", "P05"]
    schedule = generate_round_robin_schedule(players)

    print(f"\nPlayers: {players}")
    print(f"Total players: {len(players)}")

    for round_idx, round_matches in enumerate(schedule):
        print(f"\nRound {round_idx + 1}:")
        for match in round_matches:
            print(f"  {match[0]} vs {match[1]}")

        # Show who has bye (who's not playing)
        playing = set()
        for match in round_matches:
            playing.add(match[0])
            playing.add(match[1])
        bye_players = set(players) - playing
        if bye_players:
            print(f"  Bye: {', '.join(bye_players)}")

    stats = get_schedule_stats(schedule)
    print(f"\nStatistics:")
    print(f"  Total rounds: {stats['total_rounds']}")
    print(f"  Total matches: {stats['total_matches']}")


def demo_match_scheduler():
    """Demonstrate MatchScheduler with referee assignment."""
    print("\n" + "=" * 70)
    print("DEMO 3: Match Scheduler with Referee Assignment")
    print("=" * 70)

    scheduler = MatchScheduler(league_id="DEMO_LEAGUE")

    players = ["P01", "P02", "P03", "P04"]
    referees = [
        {"referee_id": "REF01", "display_name": "Referee Alpha"},
        {"referee_id": "REF02", "display_name": "Referee Beta"}
    ]

    print(f"\nPlayers: {players}")
    print(f"Referees: {[r['referee_id'] for r in referees]}")

    schedule = scheduler.create_tournament_schedule(players, referees)

    print(f"\nTournament Schedule:")
    for round_idx, round_matches in enumerate(schedule):
        print(f"\nRound {round_idx + 1}:")
        for match in round_matches:
            print(f"  {match.match_id}:")
            print(f"    Players: {match.player_a_id} vs {match.player_b_id}")
            print(f"    Referee: {match.referee_id}")

    print(f"\nReferee Workload:")
    for referee_id, count in scheduler.referee_workload.items():
        print(f"  {referee_id}: {count} matches")


def demo_large_tournament():
    """Demonstrate larger tournament (8 players)."""
    print("\n" + "=" * 70)
    print("DEMO 4: Large Tournament (8 Players, 2 Referees)")
    print("=" * 70)

    scheduler = MatchScheduler(league_id="L1")

    players = [f"P{i:02d}" for i in range(1, 9)]
    referees = [
        {"referee_id": "REF01"},
        {"referee_id": "REF02"}
    ]

    print(f"\nPlayers: {len(players)} players")
    print(f"Referees: {len(referees)} referees")

    schedule = scheduler.create_tournament_schedule(players, referees)

    print(f"\nTournament Statistics:")
    print(f"  Total rounds: {len(schedule)}")
    print(f"  Total matches: {sum(len(r) for r in schedule)}")
    print(f"  Matches per round: {len(schedule[0])}")

    print(f"\nReferee Load Balancing:")
    for referee_id, count in sorted(scheduler.referee_workload.items()):
        print(f"  {referee_id}: {count} matches")

    # Show first round only
    print(f"\nRound 1 Matches:")
    for match in schedule[0]:
        print(f"  {match.match_id}: {match.player_a_id} vs {match.player_b_id} "
              f"(Ref: {match.referee_id})")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("ROUND-ROBIN TOURNAMENT SCHEDULER DEMONSTRATION")
    print("=" * 70)

    demo_basic_schedule()
    demo_odd_players()
    demo_match_scheduler()
    demo_large_tournament()

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nAll schedules generated successfully!")
    print("The scheduler is ready for production use.\n")


if __name__ == "__main__":
    main()
