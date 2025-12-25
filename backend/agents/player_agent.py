import math
from typing import Dict, Any

from ..constants import WALKING_SPEED, HOLE_COMPLETION_DISTANCE, SHOT_TAKING_DISTANCE
from ..utils.calculations import Calculations


class PlayerAgent:
    """Golf player agent with utility-based decision making."""

    def __init__(self, id: int, accuracy: float, strength: float):
        self.id = id
        self.accuracy = accuracy
        self.strength = strength

        self.player_position = {"x": 0, "y": 0}
        self.ball_position = {"x": 0, "y": 0}
        self.strokes = 0
        self.ball_state = "at_rest"
        self.current_lie = "tee"
        self.is_complete = False

        self.state = "idle"
        self.walking_progress = 0.0  # 0 to 1 when walking to ball

    def take_shot(self, hole_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one shot."""
        self.strokes += 1
        self.state = "hitting"

        flag = hole_data["flag"]
        distance_to_flag = Calculations.get_distance(self.ball_position, flag)
        direction_to_flag = Calculations.get_direction(self.ball_position, flag)

        max_shot_distance = self._get_max_shot_distance(distance_to_flag)
        intended_power = min(max_shot_distance, distance_to_flag)

        # TODO: Implement actual_direction variation
        # TODO: Implement actual_power variation

        old_ball_position = self.ball_position.copy()
        self.ball_position = self._get_new_ball_position(
            intended_power, direction_to_flag
        )

        self.current_lie = self._determine_lie(self.ball_position, hole_data)

        self.state = "waiting"
        self.walking_progress = 0.0

        new_distance_to_flag = Calculations.get_distance(self.ball_position, flag)
        if new_distance_to_flag < HOLE_COMPLETION_DISTANCE:
            self.is_complete = True
            self.current_lie = "hole"

        return {
            "player_id": self.id,
            "stroke_number": self.strokes,
            "old_position": old_ball_position,
            "new_position": self.ball_position,
            "distance_traveled": intended_power,
            "distance_to_flag": new_distance_to_flag,
            "is_complete": self.is_complete,
        }

    def walk_to_ball(self) -> bool:
        """
        Move player towards ball. Returns True when reached.
        Call this each tick until player reaches ball.
        """
        if self.state != "walking" and self.state != "waiting":
            return True  # Already at ball

        distance = Calculations.get_distance(self.player_position, self.ball_position)

        if distance < SHOT_TAKING_DISTANCE:
            self.player_position = self.ball_position.copy()
            self.state = "idle"
            self.walking_progress = 1.0
            return True

        # Start walking if just waiting
        if self.state == "waiting":
            self.state = "walking"

        # Walk at configured speed
        direction = Calculations.get_direction(self.player_position, self.ball_position)

        move_distance = min(WALKING_SPEED, distance)
        self.player_position["x"] += move_distance * math.cos(direction)
        self.player_position["y"] += move_distance * math.sin(direction)

        # Update progress
        total_distance = Calculations.get_distance(
            {
                "x": self.player_position["x"] - move_distance * math.cos(direction),
                "y": self.player_position["y"] - move_distance * math.sin(direction),
            },
            self.ball_position,
        )
        self.walking_progress = 1.0 - (distance - move_distance) / max(
            total_distance, 1
        )

        return False

    def get_state(self) -> Dict[str, Any]:
        """
        Get current player state.
        Returns both player and ball positions for visualization.
        """
        return {
            "id": self.id,
            "position": self.player_position,
            "ball_position": self.ball_position,
            "strokes": self.strokes,
            "current_lie": self.current_lie,
            "state": self.state,
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
        new_x = self.ball_position["x"] + power * math.cos(direction)
        new_y = self.ball_position["y"] + power * math.sin(direction)

        return {"x": new_x, "y": new_y}

    def _determine_lie(
        self, position: Dict[str, float], hole_data: Dict[str, Any]
    ) -> str:
        """Determine what type of lie the ball is in."""
        if "green" in hole_data and Calculations.point_in_polygon(
            position, hole_data["green"]
        ):
            return "green"

        if "bunkers" in hole_data:
            for bunker in hole_data["bunkers"]:
                if Calculations.point_in_polygon(position, bunker):
                    return "bunker"

        if "fairway" in hole_data and Calculations.point_in_polygon(
            position, hole_data["fairway"]
        ):
            return "fairway"

        return "rough"
