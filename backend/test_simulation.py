from backend.simulation import SimulationEngine
from backend.simulation.player_group import PlayerGroup
from backend.agents import PlayerAgent


def main():
    """Run a simulation test."""
    print("\n" + "=" * 50)
    print("GOLF SIMULATION TEST")
    print("=" * 50 + "\n")

    # Create simulation engine
    engine = SimulationEngine()
    print(f"Loaded {engine.num_holes} hole(s)")

    player1 = PlayerAgent(id=1, accuracy=0.8, strength=0.9)
    player2 = PlayerAgent(id=2, accuracy=0.6, strength=0.7)
    group = PlayerGroup(
        id=1,
        players=[player1, player2],
        starting_hole=1,
        tee_time=0
    )

    # Position players at the tee
    tee_box = engine.holes[1]["tees"][0]
    for player in group.players:
        player.position = engine.get_tee_position(tee_box)

    # Add group to engine
    engine.player_groups.append(group)

    # Run simulation
    print("Starting simulation...\n")
    max_ticks = 100
    for i in range(max_ticks):
        engine.tick()

        # Check if all groups are done
        if all(g.is_complete for g in engine.player_groups):
            print("\nAll groups completed!")
            break

    # Print results
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    for player in group.players:
        print(f"Player {player.id}: {player.strokes} strokes")
    print("=" * 50 + "\n")

    print("Test complete!")


if __name__ == "__main__":
    main()
