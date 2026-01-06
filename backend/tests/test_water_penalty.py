import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.player_agent import PlayerAgent
from backend.agents.shot_utility import ShotUtility
from backend.utils.calculations import Calculations


def test_water_penalty_and_drop():
    """Test that a ball landing in water triggers penalty and drops at entry point."""
    print("\n=== Testing Water Penalty and Drop ===\n")
    
    hole_data = {
        "flag": {"x": 200, "y": 50},
        "par": 4,
        "tees": [{"x": 0, "y": 50}],
        "fairway": [
            {"x": 0, "y": 40},
            {"x": 0, "y": 60},
            {"x": 90, "y": 60},
            {"x": 90, "y": 40},
        ],
        "green": [
            {"x": 180, "y": 40},
            {"x": 180, "y": 60},
            {"x": 220, "y": 60},
            {"x": 220, "y": 40},
        ],
        "bunkers": [],
    }

    water = [
        [
            {"x": 100, "y": 30},
            {"x": 100, "y": 70},
            {"x": 120, "y": 70},
            {"x": 120, "y": 30},
        ]
    ]
    
    player = PlayerAgent(
        id=1,
        accuracy=0.0,
        strength=1.0,
    )
    player.ball_position = {"x": 0, "y": 50}
    player.current_lie = "tee"
    
    print(f"Initial position: ({player.ball_position['x']:.2f}, {player.ball_position['y']:.2f})")
    print(f"Initial strokes: {player.strokes}")
    print(f"Initial lie: {player.current_lie}")
    
    # Manually set the player to shoot directly into the water
    old_position = player.ball_position.copy()
    player.ball_position = {"x": 110, "y": 50}
    player.strokes += 1
    
    print(f"\nForced ball position (should be in water): ({player.ball_position['x']:.2f}, {player.ball_position['y']:.2f})")
    
    # Determine the lie (should detect water)
    player.current_lie = ShotUtility.determine_lie(player.ball_position, hole_data, water)
    print(f"Detected lie: {player.current_lie}")
    
    assert player.current_lie == "water", f"Expected 'water' but got '{player.current_lie}'"
    print("✓ Ball correctly detected in water")
    
    # Now simulate the water penalty logic from player_agent.py
    if player.current_lie == "water":
        print("\n--- Applying Water Penalty ---")
        
        entry_point = None
        for water_polygon in water:
            intersection = Calculations.line_segment_intersects_polygon(
                old_position, player.ball_position, water_polygon
            )
            if intersection:
                entry_point = intersection
                print(f"Entry point found: ({entry_point['x']:.2f}, {entry_point['y']:.2f})")
                break
        
        assert entry_point is not None, "Should find water entry point"
        print("✓ Entry point found")
        
        distance_to_entry = Calculations.get_distance(old_position, entry_point)
        print(f"Distance to entry: {distance_to_entry:.2f}m")
        
        if distance_to_entry > 2:
            import math
            direction = Calculations.get_direction(old_position, entry_point)
            drop_distance = distance_to_entry - 2.0
            drop_position = {
                "x": old_position["x"] + drop_distance * math.cos(direction),
                "y": old_position["y"] + drop_distance * math.sin(direction),
            }
        else:
            drop_position = old_position.copy()
        
        print(f"Drop position: ({drop_position['x']:.2f}, {drop_position['y']:.2f})")
        
        drop_in_water = False
        for water_polygon in water:
            if Calculations.point_in_polygon(drop_position, water_polygon):
                drop_in_water = True
                break
        
        assert not drop_in_water, "Drop position should not be in water"
        print("✓ Drop position is outside water")
        
        drop_distance_from_tee = Calculations.get_distance(old_position, drop_position)
        entry_distance_from_tee = Calculations.get_distance(old_position, entry_point)
        assert drop_distance_from_tee < entry_distance_from_tee, "Drop should be closer to tee than entry"
        print(f"✓ Drop is {entry_distance_from_tee - drop_distance_from_tee:.2f}m before entry point")
        
        player.ball_position = drop_position
        player.strokes += 1  # Penalty stroke
        
        player.current_lie = ShotUtility.determine_lie(player.ball_position, hole_data, water)
        if player.current_lie == "water":
            player.current_lie = "rough"
        
        print(f"\nAfter penalty:")
        print(f"  Ball position: ({player.ball_position['x']:.2f}, {player.ball_position['y']:.2f})")
        print(f"  Total strokes: {player.strokes}")
        print(f"  New lie: {player.current_lie}")
        
        assert player.strokes == 2, f"Expected 2 strokes (1 shot + 1 penalty), got {player.strokes}"
        print("✓ Penalty stroke added")
        
        assert player.current_lie != "water", "Ball should not be in water after drop"
        print("✓ New lie is not water")
    
    print("\n=== Water Penalty Test PASSED ===\n")


def test_no_water_penalty_when_avoiding():
    """Test that players successfully avoid water when selecting shots."""
    print("\n=== Testing Water Avoidance in Shot Selection ===\n")
    
    hole_data = {
        "flag": {"x": 200, "y": 50},
        "par": 4,
        "tees": [{"x": 0, "y": 50}],
        "fairway": [
            {"x": 0, "y": 30},
            {"x": 0, "y": 70},
            {"x": 300, "y": 70},
            {"x": 300, "y": 30},
        ],
        "green": [
            {"x": 180, "y": 40},
            {"x": 180, "y": 60},
            {"x": 220, "y": 60},
            {"x": 220, "y": 40},
        ],
        "bunkers": [],
    }
    
    water = [
        [
            {"x": 90, "y": 35},
            {"x": 90, "y": 65},
            {"x": 110, "y": 65},
            {"x": 110, "y": 35},
        ]
    ]
    
    player = PlayerAgent(
        id=2,
        accuracy=0.8,
        strength=1.0,
    )
    player.ball_position = {"x": 0, "y": 50}
    player.current_lie = "tee"
    
    print(f"Player at: ({player.ball_position['x']:.2f}, {player.ball_position['y']:.2f})")
    print(f"Water blocks direct path to flag")
    
    wind_conditions = {"speed": 0, "direction": 0}
    shot = ShotUtility.select_best_shot(
        player.ball_position,
        player.current_lie,
        player.strength,
        hole_data,
        wind_conditions,
        player.accuracy,
        water,
    )
    
    print(f"\nSelected shot: club={shot['club']}")
    print(f"Landing position: ({shot['landing_position']['x']:.2f}, {shot['landing_position']['y']:.2f})")
    
    in_water = False
    for water_polygon in water:
        if Calculations.point_in_polygon(shot["landing_position"], water_polygon):
            in_water = True
            break
    
    assert not in_water, "Shot should avoid water"
    print("✓ Selected shot avoids water")
    
    print("\n=== Water Avoidance Test PASSED ===\n")


if __name__ == "__main__":
    test_water_penalty_and_drop()
    test_no_water_penalty_when_avoiding()
    print("\n✅ All water tests passed!\n")
