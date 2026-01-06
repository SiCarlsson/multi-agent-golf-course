import math
import random
import logging

from typing import Dict, Any
from ..constants import (
    WALKING_SPEED,
    HOLE_COMPLETION_DISTANCE,
    SHOT_TAKING_DISTANCE,
    GREENKEEPER_SAFETY_DISTANCE_METERS,
    GROUP_SAFETY_DISTANCE_METERS,
)
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
        other_group_positions: list[Dict[str, float]] = None,
        water: list = None,
    ) -> bool:
        """Check if it's safe to take a shot (greenkeeper and other groups not in landing zone)."""
        logger.debug(
            f"Player {self.id} can_take_shot check: ball_pos=({self.ball_position['x']:.2f}, {self.ball_position['y']:.2f}), "
            f"lie={self.current_lie}, is_complete={self.is_complete}"
        )

        best_shot = ShotUtility.select_best_shot(
            self.ball_position,
            self.current_lie,
            self.strength,
            hole_data,
            wind_conditions,
            self.accuracy,
            water,
        )

        landing_position = best_shot["landing_position"]
        logger.debug(
            f"Player {self.id} best shot: club={best_shot['club']}, "
            f"landing_pos=({landing_position['x']:.2f}, {landing_position['y']:.2f})"
        )

        distance_to_greenkeeper = Calculations.get_distance(
            landing_position, greenkeeper_position
        )
        logger.debug(
            f"Player {self.id} distance to greenkeeper from landing: {distance_to_greenkeeper:.2f}m "
            f"(threshold: {GREENKEEPER_SAFETY_DISTANCE_METERS}m)"
        )
        if distance_to_greenkeeper < GREENKEEPER_SAFETY_DISTANCE_METERS:
            logger.info(
                f"Player {self.id} cannot shoot: greenkeeper too close ({distance_to_greenkeeper:.2f}m < {GREENKEEPER_SAFETY_DISTANCE_METERS}m)"
            )
            return False

        if other_group_positions:
            shot_distance = Calculations.get_distance(
                self.ball_position, landing_position
            )
            required_distance = shot_distance + GROUP_SAFETY_DISTANCE_METERS
            logger.debug(
                f"Player {self.id} checking {len(other_group_positions)} other players. "
                f"Shot distance: {shot_distance:.2f}m, required clearance: {required_distance:.2f}m"
            )

            for index, other_position in enumerate(other_group_positions):
                distance_to_other = Calculations.get_distance(
                    self.ball_position, other_position
                )
                logger.debug(
                    f"Player {self.id} vs other player {index}: distance={distance_to_other:.2f}m, "
                    f"required={required_distance:.2f}m"
                )
                if distance_to_other < required_distance:
                    logger.info(
                        f"Player {self.id} cannot shoot: other player too close "
                        f"({distance_to_other:.2f}m < {required_distance:.2f}m)"
                    )
                    return False

        logger.debug(f"Player {self.id} can shoot - all safety checks passed")
        return True

    def take_shot(
        self,
        hole_data: Dict[str, Any],
        wind_conditions: Dict[str, Any] = None,
        water: list = None,
        current_hole_number: int = None,
        all_holes: Dict[int, Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute one shot using utility-based decision making."""
        self.strokes += 1
        self.state = "hitting"

        flag = hole_data["flag"]
        distance_before = Calculations.get_distance(self.ball_position, flag)

        logger.info(
            f"Player {self.id} taking shot #{self.strokes}: "
            f"from ({self.ball_position['x']:.2f}, {self.ball_position['y']:.2f}), "
            f"distance to flag: {distance_before:.2f}m, lie: {self.current_lie}"
        )

        best_shot = ShotUtility.select_best_shot(
            self.ball_position,
            self.current_lie,
            self.strength,
            hole_data,
            wind_conditions,
            self.accuracy,
            water,
            current_hole_number,
            all_holes,
        )

        club = best_shot["club"]
        power = best_shot["power"]
        direction = best_shot["direction"]

        logger.debug(
            f"Player {self.id} shot plan: club={club}, power={power:.2f}m, "
            f"direction={direction:.2f} rad ({math.degrees(direction):.1f}°)"
        )

        inaccuracy = 1.0 - self.accuracy

        distance_spread = 0.05 + (inaccuracy * 0.15)
        actual_power = power * (1 + random.uniform(-distance_spread, distance_spread))

        direction_spread = 0.035 + (inaccuracy * 0.335)
        actual_direction = direction + random.uniform(
            -direction_spread, direction_spread
        )

        logger.debug(
            f"Player {self.id} shot execution (with inaccuracy): "
            f"actual_power={actual_power:.2f}m, actual_direction={actual_direction:.2f} rad ({math.degrees(actual_direction):.1f}°)"
        )

        old_ball_position = self.ball_position.copy()

        self.ball_position = {
            "x": self.ball_position["x"] + actual_power * math.cos(actual_direction),
            "y": self.ball_position["y"] + actual_power * math.sin(actual_direction),
        }

        logger.info(
            f"Player {self.id} ball moved: from ({old_ball_position['x']:.2f}, {old_ball_position['y']:.2f}) "
            f"to ({self.ball_position['x']:.2f}, {self.ball_position['y']:.2f})"
        )
        logger.info(
            f"Player {self.id} shooting with wind: {wind_conditions['speed']:.1f} m/s "
            f"from {wind_conditions['direction']:.1f}° (accuracy: {self.accuracy})"
        )

        self.current_lie = ShotUtility.determine_lie(
            self.ball_position, hole_data, water
        )
        logger.debug(f"Player {self.id} new lie: {self.current_lie}")

        if self.current_lie == "water":
            logger.warning(
                f"Player {self.id} ball landed in WATER at ({self.ball_position['x']:.2f}, {self.ball_position['y']:.2f})"
            )

            entry_point = None
            if water:
                for water_polygon in water:
                    intersection = Calculations.line_segment_intersects_polygon(
                        old_ball_position, self.ball_position, water_polygon
                    )
                    if intersection:
                        entry_point = intersection
                        break

            if entry_point:
                distance_to_entry = Calculations.get_distance(
                    old_ball_position, entry_point
                )
                if distance_to_entry > 1.0:
                    direction = Calculations.get_direction(
                        old_ball_position, entry_point
                    )
                    drop_distance = distance_to_entry - 2.0
                    self.ball_position = {
                        "x": old_ball_position["x"]
                        + drop_distance * math.cos(direction),
                        "y": old_ball_position["y"]
                        + drop_distance * math.sin(direction),
                    }
                else:
                    self.ball_position = old_ball_position.copy()

                logger.warning(
                    f"Player {self.id} PENALTY: Ball dropped at ({self.ball_position['x']:.2f}, {self.ball_position['y']:.2f}) "
                    f"- 2m before water entry point"
                )
            else:
                self.ball_position = old_ball_position.copy()
                logger.warning(
                    f"Player {self.id} PENALTY: Ball dropped at original position (couldn't find entry point)"
                )

            self.strokes += 1
            logger.warning(
                f"Player {self.id} penalty stroke added. Total strokes: {self.strokes}"
            )

            self.current_lie = ShotUtility.determine_lie(
                self.ball_position, hole_data, water
            )
            if self.current_lie == "water":
                self.current_lie = "rough"
            logger.info(f"Player {self.id} dropped ball lie: {self.current_lie}")

        self.state = "idle"
        self.walking_progress = 0.0

        new_distance_to_flag = Calculations.get_distance(self.ball_position, flag)
        logger.info(
            f"Player {self.id} after shot: distance to flag = {new_distance_to_flag:.2f}m "
            f"(completion threshold: {HOLE_COMPLETION_DISTANCE}m)"
        )

        if new_distance_to_flag < HOLE_COMPLETION_DISTANCE:
            self.is_complete = True
            self.current_lie = "hole"
            logger.info(
                f"Player {self.id} COMPLETED HOLE! Final distance: {new_distance_to_flag:.2f}m, "
                f"strokes: {self.strokes}"
            )
        else:
            logger.debug(
                f"Player {self.id} still playing. Distance remaining: {new_distance_to_flag:.2f}m"
            )

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
            logger.debug(
                f"Player {self.id} walk_to_ball: already in state {self.state}, returning True"
            )
            return True

        distance = Calculations.get_distance(self.player_position, self.ball_position)

        if distance < SHOT_TAKING_DISTANCE:
            self.player_position = self.ball_position.copy()
            self.state = "idle"
            self.walking_progress = 1.0
            logger.debug(
                f"Player {self.id} reached ball. Position: ({self.player_position['x']:.2f}, {self.player_position['y']:.2f})"
            )
            return True

        if self.state == "idle":
            self.state = "walking"
            logger.debug(
                f"Player {self.id} starting to walk to ball. Distance: {distance:.2f}m"
            )

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

        logger.debug(
            f"Player {self.id} walking: moved {move_distance:.2f}m, "
            f"remaining: {distance - move_distance:.2f}m, progress: {self.walking_progress:.2%}"
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
