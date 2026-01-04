import math
import random
import logging

from typing import Dict, Any
from ..constants import (
    WALKING_SPEED,
    HOLE_COMPLETION_DISTANCE,
    SHOT_TAKING_DISTANCE,
    GREENKEEPER_SAFETY_DISTANCE_METERS,
)
from .wind_agent import WindAgent
from .shot_utility import ShotUtility
from ..utils.calculations import Calculations

logger = logging.getLogger(__name__)


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
        self.walking_progress = 0.0

    def can_take_shot(
        self,
        hole_data: Dict[str, Any],
        greenkeeper_position: Dict[str, float] = None,
        wind_conditions: Dict[str, Any] = None,
    ) -> bool:
        """Check if it's safe to take a shot (greenkeeper not in landing zone)."""
        if greenkeeper_position is None:
            return True

        best_shot = ShotUtility.select_best_shot(
            self.ball_position,
            self.current_lie,
            self.strength,
            hole_data,
            wind_conditions,
            self.accuracy,
        )

        landing_position = best_shot["landing_position"]

        distance_to_greenkeeper = Calculations.get_distance(
            landing_position, greenkeeper_position
        )

        return distance_to_greenkeeper >= GREENKEEPER_SAFETY_DISTANCE_METERS

    def take_shot(
        self, hole_data: Dict[str, Any], wind_conditions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute one shot using utility-based decision making."""
        self.strokes += 1
        self.state = "hitting"

        flag = hole_data["flag"]

        best_shot = ShotUtility.select_best_shot(
            self.ball_position,
            self.current_lie,
            self.strength,
            hole_data,
            wind_conditions,
            self.accuracy,
        )

        club = best_shot["club"]
        power = best_shot["power"]
        direction = best_shot["direction"]

        inaccuracy = 1.0 - self.accuracy

        distance_spread = 0.05 + (inaccuracy * 0.15)
        actual_power = power * (1 + random.uniform(-distance_spread, distance_spread))

        direction_spread = 0.035 + (inaccuracy * 0.335)
        actual_direction = direction + random.uniform(
            -direction_spread, direction_spread
        )

        old_ball_position = self.ball_position.copy()

        self.ball_position = {
            "x": self.ball_position["x"] + actual_power * math.cos(actual_direction),
            "y": self.ball_position["y"] + actual_power * math.sin(actual_direction),
        }

        logger.info(
            f"Player {self.id} shooting with wind: {wind_conditions['speed']:.1f} m/s "
            f"from {wind_conditions['direction']:.1f}° (accuracy: {self.accuracy})"
        )

        self.current_lie = ShotUtility.determine_lie(self.ball_position, hole_data)

        self.state = "idle"
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
            "distance_traveled": power,
            "distance_to_flag": new_distance_to_flag,
            "is_complete": self.is_complete,
            "club_used": club,
        }

    def walk_to_ball(self) -> bool:
        """
        Move player towards ball. Returns True when reached.
        """
        if self.state != "walking" and self.state != "idle":
            return True

        distance = Calculations.get_distance(self.player_position, self.ball_position)

        if distance < SHOT_TAKING_DISTANCE:
            self.player_position = self.ball_position.copy()
            self.state = "idle"
            self.walking_progress = 1.0
            return True

        if self.state == "idle":
            self.state = "walking"

        direction = Calculations.get_direction(self.player_position, self.ball_position)

        move_distance = min(WALKING_SPEED, distance)
        self.player_position["x"] += move_distance * math.cos(direction)
        self.player_position["y"] += move_distance * math.sin(direction)

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
