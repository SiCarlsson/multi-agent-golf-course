import math
from typing import Dict, Any

from ..utils.calculations import Calculations


class PlayerAgent:
    """Golf player agent with utility-based decision making."""

    def __init__(self, id: int, accuracy: float, strength: float):
        self.id = id
        self.accuracy = accuracy
        self.strength = strength

        # Game state
        self.position = {"x": 0, "y": 0}
        self.strokes = 0
        self.ball_state = "at_rest"
        self.current_lie = "tee"
        self.is_complete = False

    def take_shot(self, hole_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one shot."""
        self.strokes += 1

        flag = hole_data["flag"]
        distance_to_flag = Calculations.get_distance(self.position, flag)
        direction_to_flag = Calculations.get_direction(self.position, flag)

        max_shot_distance = self._get_max_shot_distance(distance_to_flag)
        intended_power = min(max_shot_distance, distance_to_flag)

        # TODO: Implement actual_direction variation
        # TODO: Implement actual_power variation

        old_position = self.position.copy()
        self.position = self._get_new_ball_position(intended_power, direction_to_flag)

        new_distance_to_flag = Calculations.get_distance(self.position, flag)
        if new_distance_to_flag < 1.0:  # Within 1 meter of the hole
            self.is_complete = True

        return {
            "player_id": self.id,
            "stroke_number": self.strokes,
            "old_position": old_position,
            "new_position": self.position,
            "distance_traveled": intended_power,
            "distance_to_flag": new_distance_to_flag,
            "is_complete": self.is_complete,
        }

    def get_state(self) -> Dict[str, Any]:
        """
        Get current player state.
        TODO: Return all relevant state for visualization
        """
        return {
            "id": self.id,
            "position": self.position,
            "strokes": self.strokes,
            "current_lie": self.current_lie,
        }

    def _get_max_shot_distance(self, distance_to_hole):
        """Get how far the player can hit."""
        base_max = 220  # meters (driver distance)

        if distance_to_hole < 200:
            return distance_to_hole * 1.1  # Slight overshoot possible

        return base_max * self.strength

    def _get_new_ball_position(
        self, power: float, direction: float
    ) -> Dict[str, float]:
        """Calculate new ball position based on shot power and direction."""
        new_x = self.position["x"] + power * math.cos(direction)
        new_y = self.position["y"] + power * math.sin(direction)

        return {"x": new_x, "y": new_y}
